from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, ConnectEvent
import asyncio

client = TikTokLiveClient(unique_id="@windahbasudara14_")

@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    print(f"Connected to @{event.unique_id}!")

@client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    print(f"{event.user_info.nickname}: {event.comment}")

if __name__ == "__main__":
    client.run()