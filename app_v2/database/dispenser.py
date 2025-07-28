import asyncio
import json

from app_v2.database.postgre_db import Postgre_db


agent_registry = {}
channel_name = "agent_notifications"

class Dispenser:

    @staticmethod
    async def register_agent(agent):
        if agent.uid not in agent_registry:
            agent_registry[agent.uid] = agent
            print(f"✅ Agent {agent.uid} registered.")
        else:
            print(f"⚠️ Agent {agent.uid} already registered.")

    @staticmethod
    async def unregister_agent(uid):
        if uid in agent_registry:
            del agent_registry[uid]
            print(f"🛑 Agent {uid} unregistered.")

    @staticmethod
    def on_notify(connection, pid, channel, payload):
        print(f"[NOTIFY] 📣 Kanał: {channel}, Payload: {payload}")
        try:
            data = json.loads(payload)
            if data.get("event") == "relation_update":
                target_uid = data.get("target")
                agent = agent_registry.get(target_uid)
                if agent:
                    try:
                        asyncio.create_task(agent.receive(data))
                        print(f"📤 Event wysłany do agenta: {target_uid}")
                    except Exception as e:
                        print(f"❌ Agent {target_uid} nie przyjął eventu: {e}")
                else:
                    print(f"🔍 Brak agenta dla UID: {target_uid}")
        except json.JSONDecodeError:
            print("⚠️ Nieprawidłowy JSON w payload")

    @staticmethod
    async def listen_to_channel():
        pool = await Postgre_db.get_db_pool()
        if not pool:
            print("❌ Brak połączenia z bazą.")
            return

        async with pool.acquire() as conn:
            await conn.execute(f"LISTEN {channel_name}")
            await conn.add_listener(channel_name, Dispenser.on_notify)
            print(f"🔔 Nasłuchiwanie kanału '{channel_name}' aktywne...")

            while True:
                await asyncio.sleep(3600)  # keep connection alive
