import asyncio
import uuid
from typing import Dict, Set, List
from theme_keywords import THEME_KEYWORDS

from log_utils import section
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message


class CommunityAgent(Agent):
    def __init__(self, jid, password, room_label, cm_jid):
        super().__init__(jid, password)
        self.room_label = room_label
        self.cm_jid = cm_jid
        # theme -> set of member JIDs
        self.communities: Dict[str, Set[str]] = {}
        self.jid_str = str(jid)

        # conversation_id -> { "expected", "responses", "future" }
        self.pending_queries: Dict[str, Dict] = {}
        self.query_timeout = 10.0

    # REGISTRATION

    class RegistrationBehav(OneShotBehaviour):
        async def run(self):
            msg = Message(to=self.agent.cm_jid)
            msg.set_metadata("performative", "register")
            msg.body = "Smart room"
            await self.send(msg)

            section(
                f"[{self.agent.room_label}] REGISTRATION SENT\n"
                f"  → To CM: {self.agent.cm_jid}"
            )

    # GENERIC MESSAGE HANDLER

    class MessageHandlerBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if msg:
                await self.handle_message(msg)

        async def handle_message(self, msg: Message):
            agent: "CommunityAgent" = self.agent
            t = msg.metadata.get("type")

            if t == "community_update":
                await self.handle_community_update(msg)
                return

            if t == "community_join_invite":
                await self.handle_join_invite(msg)
                return

            if t == "community_form_proposal":
                await self.handle_form_proposal(msg)
                return

            if t in ("community_join_ack", "community_created_ack"):
                await self.handle_community_update(msg)
                return

            if t == "query":
                reply = msg.make_reply()
                reply.set_metadata("type", "answer")

                conv_id = msg.metadata.get("conversation_id")
                if conv_id:
                    reply.set_metadata("conversation_id", conv_id)

                reply.body = (
                    f"[{agent.room_label}] I do not have a specific answer (mock-up)."
                )

                section(
                    f"[{agent.room_label}] DEFAULT ANSWER SENT\n"
                    f"  → To: {msg.sender}\n"
                    f"  → Body: {reply.body}"
                )
                await self.send(reply)
                return

            if t == "answer":
                await self.handle_answer(msg)
                return

            section(
                f"[{agent.room_label}] MESSAGE RECEIVED (UNHANDLED TYPE)\n"
                f"  → From: {msg.sender}\n"
                f"  → Type: {t}\n"
                f"  → Body: {msg.body}"
            )

        async def handle_community_update(self, msg: Message):
            agent: "CommunityAgent" = self.agent
            theme = msg.metadata.get("theme")
            members_meta = msg.metadata.get("members_jids", "")

            members = members_meta.split(",") if members_meta else []
            agent.communities[theme] = set(members)

            section(
                f"[{agent.room_label}] COMMUNITY UPDATE\n"
                f"  → Theme: {theme}\n"
                f"  → Members:\n" +
                "".join(f"    - {m}\n" for m in members)
            )

        async def handle_join_invite(self, msg: Message):
            agent: "CommunityAgent" = self.agent
            theme = msg.metadata.get("theme", "unknown")

            section(
                f"[{agent.room_label}] JOIN INVITATION RECEIVED\n"
                f"  → Theme: {theme}\n"
                f"  → From CM: {msg.sender}\n"
                f"  → Decision: AUTO-ACCEPT"
            )

            reply = Message(to=str(msg.sender))
            reply.set_metadata("type", "community_join_response")
            reply.set_metadata("theme", theme)
            reply.set_metadata("decision", "accept")
            reply.body = f"{agent.room_label} accepts to join community '{theme}'."
            await self.send(reply)

        async def handle_form_proposal(self, msg: Message):
            agent: "CommunityAgent" = self.agent
            theme = msg.metadata.get("theme", "unknown")

            section(
                f"[{agent.room_label}] FORM PROPOSAL RECEIVED\n"
                f"  → Theme: {theme}\n"
                f"  → From CM: {msg.sender}\n"
                f"  → Decision: AUTO-ACCEPT"
            )

            reply = Message(to=str(msg.sender))
            reply.set_metadata("type", "community_form_response")
            reply.set_metadata("theme", theme)
            reply.set_metadata("decision", "accept")
            reply.body = f"{agent.room_label} accepts to form community '{theme}'."
            await self.send(reply)

        async def handle_answer(self, msg: Message):
            agent: "CommunityAgent" = self.agent
            conv_id = msg.metadata.get("conversation_id")

            section(
                f"[{agent.room_label}] ANSWER RECEIVED\n"
                f"  → From: {msg.sender}\n"
                f"  → Conversation ID: {conv_id}\n"
                f"  → Body: {msg.body}"
            )

            if not conv_id:
                return

            if conv_id not in agent.pending_queries:
                return

            data = agent.pending_queries[conv_id]
            data["responses"][str(msg.sender)] = msg.body

            expected = data["expected"]
            future: asyncio.Future = data["future"]

            if set(data["responses"].keys()) >= expected and not future.done():
                future.set_result(data["responses"])
                del agent.pending_queries[conv_id]

    def get_relevant_communities(self, query: str) -> List[str]:
        q_raw = query or ""
        q = q_raw.lower()
        words = set(q.split())

        scores = {}

        for theme in self.communities.keys():
            theme_l = theme.lower()
            score = 0

            if theme_l in q:
                score += 1

            keywords = THEME_KEYWORDS.get(theme, set())
            for kw in keywords:
                if kw in q or kw in words:
                    score += 1

            if score > 0:
                scores[theme] = score

        # Sort themes by score desc, then alphabetically
        ordered = sorted(scores.keys(), key=lambda t: (-scores[t], t))

        section(
            f"[{self.room_label}] RELEVANT COMMUNITIES\n"
            f"  → Query: {q_raw}\n"
            f"  → Scored themes:\n" +
            (
                "".join(
                    f"    - {theme} (score={scores[theme]})\n"
                    for theme in ordered
                )
                if ordered
                else "    (no relevant communities)\n"
            )
        )

        return ordered

    async def ask_community(self, behaviour, community: str, query: str) -> Dict[str, str]:
        members = self.communities.get(community, set())
        # exclude self
        targets = {m for m in members if m != self.jid_str}

        if not targets:
            section(
                f"[{self.room_label}] ASK COMMUNITY\n"
                f"  → Community: {community}\n"
                f"  → Query: {query}\n"
                f"  → No other members to ask."
            )
            return {}

        conv_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        fut = loop.create_future()

        self.pending_queries[conv_id] = {
            "expected": set(targets),
            "responses": {},
            "future": fut,
        }

        section(
            f"[{self.room_label}] ASK COMMUNITY\n"
            f"  → Community: {community}\n"
            f"  → Conversation ID: {conv_id}\n"
            f"  → Query: {query}\n"
            f"  → Targets:\n" +
            "".join(f"    - {t}\n" for t in targets)
        )

        # send queries via BEHAVIOUR, not agent
        for t in targets:
            msg = Message(to=t)
            msg.set_metadata("type", "query")
            msg.set_metadata("theme", community)
            msg.set_metadata("conversation_id", conv_id)
            msg.body = query
            await behaviour.send(msg)

        # wait for answers with timeout
        try:
            responses = await asyncio.wait_for(fut, timeout=self.query_timeout)

            section(
                f"[{self.room_label}] ASK COMMUNITY – COMPLETED\n"
                f"  → Community: {community}\n"
                f"  → Conversation ID: {conv_id}\n"
                f"  → Responses:\n" +
                "".join(f"    - {sender}: {body}\n" for sender, body in responses.items())
            )
            return responses

        except asyncio.TimeoutError:
            data = self.pending_queries.pop(conv_id, None)
            if data:
                section(
                    f"[{self.room_label}] ASK COMMUNITY – TIMEOUT\n"
                    f"  → Community: {community}\n"
                    f"  → Conversation ID: {conv_id}\n"
                    f"  → Partial responses:\n" +
                    "".join(
                        f"    - {sender}: {body}\n"
                        for sender, body in data["responses"].items()
                    )
                )
                return data["responses"]
            return {}

    async def setup(self):
        section(
            f"[{self.room_label}] COMMUNITY AGENT STARTING\n"
            f"  → JID: {self.jid}"
        )
        self.add_behaviour(self.RegistrationBehav())
        self.add_behaviour(self.MessageHandlerBehav())
