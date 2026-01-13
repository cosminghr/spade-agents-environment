import asyncio

from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message

from agents_base import CommunityAgent


class Room308Agent(CommunityAgent):
    class ScenarioBehav(OneShotBehaviour):
        async def run(self):
            agent = self.agent
            await asyncio.sleep(10)

            theme1 = "south exposure"
            targets = [m for m in agent.communities.get(theme1, set()) if m != agent.jid_str]

            q1 = (
                "If it is sunny and hot outside and I want to keep 20°C inside, "
                "is it a good idea to open the blinds just to get more light?"
            )

            for t in targets:
                msg = Message(to=t)
                msg.set_metadata("type", "query")
                msg.set_metadata("theme", theme1)
                msg.body = q1
                print(f"[Room308] QUERY -> {t}: {q1}")
                await self.send(msg)

            await asyncio.sleep(8)

            q2 = (
                "What alternatives do I have to increase the light in the room "
                "if I do not want to open the blinds because of the heat?"
            )

            for t in targets:
                msg = Message(to=t)
                msg.set_metadata("type", "query")
                msg.set_metadata("theme", theme1)
                msg.body = q2
                print(f"[Room308] QUERY -> {t}: {q2}")
                await self.send(msg)

            await asyncio.sleep(8)

            theme2 = "smart lamp"
            targets2 = [m for m in agent.communities.get(theme2, set()) if m != agent.jid_str]

            q3 = (
                "How can I make the room brighter using only the smart lighting system?"
            )

            for t in targets2:
                msg = Message(to=t)
                msg.set_metadata("type", "query")
                msg.set_metadata("theme", theme2)
                msg.body = q3
                print(f"[Room308] QUERY -> {t}: {q3}")
                await self.send(msg)

    async def setup(self):
        await super().setup()
        self.add_behaviour(self.ScenarioBehav())


class Room408Agent(CommunityAgent):
    class CustomHandlerBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if msg:
                await self.handle(msg)

        async def handle(self, msg: Message):
            t = msg.metadata.get("type")

            if t == "community_update":
                await CommunityAgent.MessageHandlerBehav.handle_community_update(self, msg)
                return

            if t == "query":
                body = msg.body or ""
                reply = msg.make_reply()
                reply.set_metadata("type", "answer")

                if "good idea to open the blinds" in body:
                    reply.body = (
                        "No, it is not a good idea to open the blinds, "
                        "because the room will become too hot."
                    )
                elif "What alternatives do I have" in body:
                    reply.body = "I do not know any alternative solutions (mock-up)."
                else:
                    reply.body = "I do not have a specific answer (mock-up)."

                print(f"[Room408] ANSWER -> {msg.sender}: {reply.body}")
                await self.send(reply)
                return

            print(f"[Room408] MESSAGE from {msg.sender}: {msg.body}")

    async def setup(self):
        self.add_behaviour(self.RegistrationBehav())
        self.add_behaviour(self.CustomHandlerBehav())


class Room701Agent(CommunityAgent):
    class CustomHandlerBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if msg:
                await self.handle(msg)

        async def handle(self, msg: Message):
            t = msg.metadata.get("type")

            if t == "community_update":
                await CommunityAgent.MessageHandlerBehav.handle_community_update(self, msg)
                return

            if t == "query":
                body = msg.body or ""
                reply = msg.make_reply()
                reply.set_metadata("type", "answer")

                if "make the room brighter" in body:
                    reply.body = (
                        "You can increase the intensity of the smart lamp in the room."
                    )
                else:
                    reply.body = "I do not have a specific answer (mock-up)."

                print(f"[Room701] ANSWER -> {msg.sender}: {reply.body}")
                await self.send(reply)
                return

            print(f"[Room701] MESSAGE from {msg.sender}: {msg.body}")

    async def setup(self):
        self.add_behaviour(self.RegistrationBehav())
        self.add_behaviour(self.CustomHandlerBehav())
