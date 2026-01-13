# main.py
import asyncio
import spade

from config import ACCOUNTS
from communities_manager import CommunitiesManager
from community_agent import CommunityAgent
from room308_agent import Room308Agent
from room408_agent import Room408Agent
from room701_agent import Room701Agent

# (restul camerelor generice folosesc CommunityAgent)
AGENT_CONFIG = [
    ("room308", Room308Agent,  "Room308", 10001),
    ("room408", Room408Agent,  "Room408", 10002),
    ("lobby",   CommunityAgent, "Lobby",  10003),
    ("room304", CommunityAgent, "Room304", 10004),
    ("room506", CommunityAgent, "Room506", 10005),
    ("room701", Room701Agent,  "Room701", 10006),
]


async def main():
    # CM
    cm = CommunitiesManager(*ACCOUNTS["cm"])
    await cm.start(auto_register=True)
    cm.web.start(hostname="127.0.0.1", port=10000)
    print("[UI] CommunitiesManager running at http://127.0.0.1:10000/spade")

    agents = []

    for account_key, AgentClass, room_label, ui_port in AGENT_CONFIG:
        agent = AgentClass(
            *ACCOUNTS[account_key],
            room_label=room_label,
            cm_jid=ACCOUNTS["cm"][0],
        )
        await agent.start(auto_register=True)
        agent.web.start(hostname="127.0.0.1", port=ui_port)
        print(f"[UI] {room_label} ({AgentClass.__name__}) running at http://127.0.0.1:{ui_port}/spade")
        agents.append(agent)

    print("\nAll agents started. Press CTRL+C to stop.\n")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nCTRL+C detected. Shutting down all agents...\n")

        for agent in agents:
            await agent.stop()
        await cm.stop()

        await asyncio.sleep(1)
        print("All agents stopped cleanly.")


if __name__ == "__main__":
    spade.run(main())
