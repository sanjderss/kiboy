import asyncio
import websockets
import json

async def trigger():
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        await ws.send(json.dumps({"action": "start_login", "account": "Email: iztammdx@guerrillamail.info | User: bot_iztammdx | Pass: Bot123456!"}))
        print("Bot started via WS!")
        try:
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get("type") == "log":
                    print(f"LOG: {data.get('content')}")
                if "MISI SELESAI" in data.get("content", "") or "Selesai" in data.get("content", ""):
                    print("Finished!")
                    break
        except websockets.ConnectionClosed:
            print("WS Closed.")
            
asyncio.run(trigger())
