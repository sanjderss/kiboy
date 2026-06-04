import asyncio
import websockets
import json

async def test_bot():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # Send start_login
        payload = {
            "action": "start_login",
            "account": "Email: bwgnypzf@guerrillamail.info | User: bot_bwgnypzf | Pass: Bot123456!"
        }
        await websocket.send(json.dumps(payload))
        
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            if data["type"] == "log":
                print(f"[{data.get('type')}] {data.get('content')}")
            elif data["type"] == "debug_image":
                print(f"[DEBUG_IMAGE RECEIVED]")
            elif data["type"] == "image":
                pass # skip screen stream to not flood terminal
            elif data["type"] == "status":
                print(f"STATUS: {data.get('content')}")
                if data.get('content') == "Idle":
                    break

if __name__ == "__main__":
    asyncio.run(test_bot())
