import asyncio
from fastapi import FastAPI, WebSocket
from TikTokLive import TikTokLiveClient
from TikTokLive.events import (
    ConnectEvent,
    DisconnectEvent,
    GiftEvent,
    CommentEvent,
    FollowEvent,
)

app = FastAPI()
connections = []
username = "quangluxubulivetiktok"
# username = "poro.live"


client = TikTokLiveClient(unique_id=username)


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        connections.remove(websocket)


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    print(f"From Tiktok: Connected to @{event.unique_id} (Room ID: {client.room_id})")


@client.on(DisconnectEvent)
async def on_disconnect(event: DisconnectEvent):
    print("From Tiktok: Disconnected")


@client.on(GiftEvent)
async def on_gift(event: GiftEvent):

    # Nếu đang combo thì bỏ qua
    if getattr(event, "streaking", False):
        return

    user = event.from_user

    data = {
        "event": "GIFT",
        "user_id": user.id,
        "username": user.username,
        "nickname": user.nick_name,
        "gift": event.gift.name,
        "gift_id": event.gift.id,
        "count": event.repeat_count,
        "diamonds": event.gift.diamond_count,
    }
    print(f"Received gift: {data['gift_id']} - {data['gift']} - {data['diamonds']}")

    for ws in connections:
        await ws.send_json(data)


@client.on(FollowEvent)
async def on_follow(event: FollowEvent):
    data = {
        "event": "SPEECH",
        "text": "Thanks for your follow",
    }

    for ws in connections:
        await ws.send_json(data)


async def client_manager():
    while True:
        try:
            print("Attempting to connect...")
            await client.start()
            break
        except Exception as e:
            print(f"Client error: {e}")

        print("Retrying in 15 seconds...")
        await asyncio.sleep(15)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(client_manager())
