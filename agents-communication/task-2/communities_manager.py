from __future__ import annotations

import asyncio
from typing import Dict, Set
from log_utils import banner, section
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

from config import THEMES, short_name_from_jid


class CommunitiesManager(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.short_to_jid: Dict[str, str] = {}
        self.communities: Dict[str, Set[str]] = {}
        self.pending_forms: Dict[str, Dict[str, bool | None]] = {}

    class ManagerBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if not msg:
                return

            performative = msg.metadata.get("performative")
            mtype = msg.metadata.get("type")

            if performative == "register":
                await self.handle_registration(msg)
            elif mtype == "community_join_response":
                await self.handle_join_response(msg)
            elif mtype == "community_form_response":
                await self.handle_form_response(msg)

        async def handle_registration(self, msg: Message):
            agent: "CommunitiesManager" = self.agent
            full_jid = str(msg.sender)
            short = short_name_from_jid(full_jid)

            agent.short_to_jid[short] = full_jid
            print(f"[CM] Registration from {full_jid} (short='{short}')")

            for theme, members_short in THEMES.items():
                if short not in members_short:
                    continue

                other_shorts = [
                    s for s in members_short
                    if s in agent.short_to_jid and s != short
                ]

                # Case 1: community already exists => invite this agent to join
                if theme in agent.communities and agent.communities[theme]:
                    print(f"[CM] Agent {short} fits existing community '{theme}'. Sending join invite.")
                    await self.send_join_invite(full_jid, theme)
                    continue

                # Case 2: no community yet, but at least one other known agent => propose forming a community
                if other_shorts:
                    participant_shorts = set(other_shorts + [short])
                    print(
                        f"[CM] Agents {participant_shorts} match theme '{theme}' "
                        f"but no community yet. Sending form proposals."
                    )
                    await self.send_form_proposals(theme, participant_shorts)

        async def send_join_invite(self, full_jid: str, theme: str):
            invite = Message(to=full_jid)
            invite.set_metadata("type", "community_join_invite")
            invite.set_metadata("theme", theme)
            invite.body = f"Do you want to join community '{theme}'?"
            await self.send(invite)

        async def send_form_proposals(self, theme: str, participant_shorts: Set[str]):
            agent: "CommunitiesManager" = self.agent

            # initialize / extend pending forms for this theme
            theme_votes = agent.pending_forms.get(theme, {})
            for s in participant_shorts:
                if s not in theme_votes:
                    theme_votes[s] = None
            agent.pending_forms[theme] = theme_votes

            # send proposal to all participants
            for s in participant_shorts:
                dest = agent.short_to_jid.get(s)
                if not dest:
                    continue
                msg = Message(to=dest)
                msg.set_metadata("type", "community_form_proposal")
                msg.set_metadata("theme", theme)
                msg.body = (
                    f"Do you agree to form a new community with theme '{theme}'?"
                )
                await self.send(msg)

        async def handle_join_response(self, msg: Message):
            agent: "CommunitiesManager" = self.agent
            full_jid = str(msg.sender)
            short = short_name_from_jid(full_jid)
            theme = msg.metadata.get("theme")
            decision = msg.metadata.get("decision", "reject")

            if not theme:
                return

            print(
                f"[CM] Join response from {short} for theme '{theme}': {decision}"
            )

            if decision != "accept":
                return

            members = agent.communities.setdefault(theme, set())
            members.add(full_jid)

            # broadcast update to all members
            await self.broadcast_community_update(theme)

        async def handle_form_response(self, msg: Message):
            agent: "CommunitiesManager" = self.agent
            full_jid = str(msg.sender)
            short = short_name_from_jid(full_jid)
            theme = msg.metadata.get("theme")
            decision = msg.metadata.get("decision", "reject")

            if not theme or theme not in agent.pending_forms:
                return

            print(
                f"[CM] Form response from {short} for theme '{theme}': {decision}"
            )

            votes = agent.pending_forms[theme]
            if short not in votes:
                return

            votes[short] = (decision == "accept")

            # Count acceptances
            accepted_count = sum(1 for v in votes.values() if v)
            all_replied = all(v is not None for v in votes.values())

            # If at least 2 accept => create community
            if accepted_count >= 2:
                full_members = {
                    agent.short_to_jid[s]
                    for s, v in votes.items()
                    if v and s in agent.short_to_jid
                }
                agent.communities[theme] = full_members
                print(
                    f"[CM] Community '{theme}' created with members: {full_members}"
                )
                await self.broadcast_community_update(theme)
                del agent.pending_forms[theme]

            elif all_replied:
                print(
                    f"[CM] Community '{theme}' not created (not enough acceptances)."
                )
                del agent.pending_forms[theme]

        async def broadcast_community_update(self, theme: str):
            agent: "CommunitiesManager" = self.agent
            members = agent.communities.get(theme, set())
            if not members:
                return

            members_list = sorted(members)
            for dest in members_list:
                notify = Message(to=dest)
                notify.set_metadata("type", "community_update")
                notify.set_metadata("theme", theme)
                notify.set_metadata("members_jids", ",".join(members_list))
                notify.body = f"Community '{theme}' members updated."
                await self.send(notify)
            print(f"[CM] Broadcasted community '{theme}' update to {members_list}.")

    async def setup(self):
        banner(f"[CM] CommunitiesManager starting as {self.jid}")
        self.add_behaviour(self.ManagerBehav())
