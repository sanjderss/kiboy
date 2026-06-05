import asyncio
import websockets
import json

async def trigger():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri, ping_interval=30, ping_timeout=600) as ws:
        await ws.send(json.dumps({"action": "start"}))
        print(f"🚀 Bot STARTED in REGISTER mode!")
        
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
