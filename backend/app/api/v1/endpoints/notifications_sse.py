# app/api/routes/notifications_sse.py

import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis

from app.core.dependencies import (
    CurrentContextFromToken,
    get_redis,
)

router = APIRouter(tags=["notifications"])


@router.get("/stream")
async def notification_stream(
    ctx: CurrentContextFromToken,
    redis_client: Redis = Depends(get_redis),
):
    async def event_generator():
        pubsub = redis_client.pubsub()
        channel = f"notifications:{ctx.user.id}"
        await pubsub.subscribe(channel)

        try:
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message["type"] == "message":
                    data = message["data"]
                    yield f"data: {data}\n\n"
                else:
                    # Heartbeat каждую секунду чтобы соединение не закрылось
                    yield ": heartbeat\n\n"
                    await asyncio.sleep(1)
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
