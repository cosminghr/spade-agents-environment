# room308_agent.py
import asyncio

from spade.behaviour import OneShotBehaviour
from log_utils import section

from community_agent import CommunityAgent


class Room308Agent(CommunityAgent):
    class ScenarioBehav(OneShotBehaviour):
        async def run(self):
            agent: "Room308Agent" = self.agent

            section(
                "[Room308] SCENARIO STARTED\n"
                "  → Waiting 10 seconds for communities to stabilize..."
            )
            await asyncio.sleep(10)

            # Q1 – south exposure

            theme1 = "south exposure"
            q1 = (
                "If it is sunny and hot outside and I want to keep 20°C inside, "
                "is it a good idea to open the blinds just to get more light?"
            )

            # AICI chemăm get_relevant_communities
            agent.get_relevant_communities(q1)

            section(
                "[Room308] SCENARIO – QUESTION 1\n"
                f"  → Community: {theme1}\n"
                f"  → Question: {q1}"
            )
            answers_q1 = await agent.ask_community(self, theme1, q1)

            section(
                "[Room308] SCENARIO – ANSWERS FOR Q1\n"
                f"  → Community: {theme1}\n" +
                (
                    "".join(
                        f"    - {sender}: {ans}\n"
                        for sender, ans in answers_q1.items()
                    )
                    if answers_q1
                    else "    (no answers)\n"
                )
            )

            await asyncio.sleep(8)

            # Q2 – south exposure

            q2 = (
                "What alternatives do I have to increase the light in the room "
                "if I do not want to open the blinds because of the heat?"
            )

            agent.get_relevant_communities(q2)

            section(
                "[Room308] SCENARIO – QUESTION 2\n"
                f"  → Community: {theme1}\n"
                f"  → Question: {q2}"
            )
            answers_q2 = await agent.ask_community(self, theme1, q2)

            section(
                "[Room308] SCENARIO – ANSWERS FOR Q2\n"
                f"  → Community: {theme1}\n" +
                (
                    "".join(
                        f"    - {sender}: {ans}\n"
                        for sender, ans in answers_q2.items()
                    )
                    if answers_q2
                    else "    (no answers)\n"
                )
            )

            await asyncio.sleep(8)

            # Q3 – smart lamp

            theme2 = "smart lamp"
            q3 = "How can I make the room brighter using only the smart lighting system?"

            agent.get_relevant_communities(q3)

            section(
                "[Room308] SCENARIO – QUESTION 3\n"
                f"  → Community: {theme2}\n"
                f"  → Question: {q3}"
            )
            answers_q3 = await agent.ask_community(self, theme2, q3)

            section(
                "[Room308] SCENARIO – ANSWERS FOR Q3\n"
                f"  → Community: {theme2}\n" +
                (
                    "".join(
                        f"    - {sender}: {ans}\n"
                        for sender, ans in answers_q3.items()
                    )
                    if answers_q3
                    else "    (no answers)\n"
                )
            )

    async def setup(self):
        await super().setup()
        self.add_behaviour(self.ScenarioBehav())
