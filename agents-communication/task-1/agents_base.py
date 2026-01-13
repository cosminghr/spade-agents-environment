from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message

from config import THEMES, short_name_from_jid


class CommunitiesManager(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.short_to_jid = {}
        self.communities = {}

    class RegistrationBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if msg and msg.metadata.get("performative") == "register":
                await self.handle_registration(msg)

        async def handle_registration(self, msg: Message):
            agent = self.agent
            full_jid = str(msg.sender)
            short = short_name_from_jid(full_jid)

            agent.short_to_jid[short] = full_jid

            for theme, members_short in THEMES.items():
                if short in members_short:
                    full_members = {
                        agent.short_to_jid[s]
                        for s in members_short
                        if s in agent.short_to_jid
                    }
                    agent.communities[theme] = full_members

                    for dest in full_members:
                        notify = Message(to=dest)
                        notify.set_metadata("type", "community_update")
                        notify.set_metadata("theme", theme)
                        notify.set_metadata("members_jids", ",".join(sorted(full_members)))
                        notify.body = f"Community '{theme}' has been updated."
                        await self.send(notify)

    async def setup(self):
        self.add_behaviour(self.RegistrationBehav())


class CommunityAgent(Agent):
    def __init__(self, jid, password, room_label, cm_jid):
        super().__init__(jid, password)
        self.room_label = room_label
        self.cm_jid = cm_jid
        self.communities = {}
        self.jid_str = str(jid)

    class RegistrationBehav(OneShotBehaviour):
        async def run(self):
            msg = Message(to=self.agent.cm_jid)
            msg.set_metadata("performative", "register")
            msg.body = "Smart room"
            await self.send(msg)

    class MessageHandlerBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if msg:
                await self.handle_message(msg)

        async def handle_message(self, msg: Message):
            agent = self.agent
            t = msg.metadata.get("type")

            if t == "community_update":
                await self.handle_community_update(msg)
                return

            if t == "query":
                reply = msg.make_reply()
                reply.set_metadata("type", "answer")
                reply.body = f"[{agent.room_label}] I do not have a specific answer (mock-up)."
                await self.send(reply)
                return

            if t == "answer":
                print(f"[{agent.room_label}] ANSWER from {msg.sender}: {msg.body}")
                return

        async def handle_community_update(self, msg: Message):
            agent = self.agent
            theme = msg.metadata["theme"]
            members = msg.metadata["members_jids"].split(",") if msg.metadata.get("members_jids") else []
            agent.communities[theme] = set(members)

            print(f"[{agent.room_label}] Community '{theme}' members:")
            for m in members:
                print(f"  - {m}")

    async def setup(self):
        self.add_behaviour(self.RegistrationBehav())
        self.add_behaviour(self.MessageHandlerBehav())
