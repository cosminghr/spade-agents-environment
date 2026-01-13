from spade.behaviour import CyclicBehaviour
from spade.message import Message
from log_utils import section

from community_agent import CommunityAgent


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

            if t == "community_join_invite":
                await CommunityAgent.MessageHandlerBehav.handle_join_invite(self, msg)
                return

            if t == "community_form_proposal":
                await CommunityAgent.MessageHandlerBehav.handle_form_proposal(self, msg)
                return

            if t == "query":
                body = msg.body or ""
                reply = msg.make_reply()
                reply.set_metadata("type", "answer")

                conv_id = msg.metadata.get("conversation_id")
                if conv_id:
                    reply.set_metadata("conversation_id", conv_id)

                if "good idea to open the blinds" in body:
                    reply.body = (
                        "No, it is not a good idea to open the blinds, "
                        "because the room will become too hot."
                    )
                elif "What alternatives do I have" in body:
                    reply.body = "I do not know any alternative solutions (mock-up)."
                else:
                    reply.body = "I do not have a specific answer (mock-up)."

                section(
                    "[Room408] CUSTOM ANSWER SENT\n"
                    f"  → To: {msg.sender}\n"
                    f"  → Body: {reply.body}"
                )
                await self.send(reply)
                return

            if t == "answer":
                await CommunityAgent.MessageHandlerBehav.handle_answer(self, msg)
                return

            section(
                "[Room408] MESSAGE RECEIVED (UNHANDLED TYPE)\n"
                f"  → From: {msg.sender}\n"
                f"  → Type: {t}\n"
                f"  → Body: {msg.body}"
            )

    async def setup(self):
        self.add_behaviour(self.RegistrationBehav())
        self.add_behaviour(self.CustomHandlerBehav())
