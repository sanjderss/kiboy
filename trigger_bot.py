import asyncio
import websockets
import json

ACCOUNT = "Email: ogboqact@spam4.me | User: bot_ogboqact | Pass: Bot123456!"

async def trigger():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri, ping_interval=30, ping_timeout=600) as ws:
        await ws.send(json.dumps({"action": "start_login", "account": ACCOUNT}))
        print(f"🚀 Bot STARTED! Akun: bot_ogboqact")
        
        try:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=600)
                data = json.loads(msg)
                if data.get("type") == "log":
                    print(f"  📝 {data['content']}")
                elif data.get("type") == "status":
                    print(f"  ⚡ STATUS: {data['content']}")
                
                content = data.get("content", "")
                if "MISI SELESAI" in content or "Bot Stopped" in content:
                    print(f"\n🏁 BOT SELESAI!")
                    break
        except asyncio.TimeoutError:
            print("⏰ Timeout 10 menit")
        except websockets.ConnectionClosed:
            print("❌ WS Disconnected")

asyncio.run(trigger())
