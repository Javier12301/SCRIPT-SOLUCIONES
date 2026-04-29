from __future__ import annotations

import json
import time
from collections.abc import Generator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_current_user
from app.db.models import User
from app.services import get_event_bus

router = APIRouter()


def _sse_encode(*, event_name: str, payload: dict) -> str:
    return f"event: {event_name}\ndata: {json.dumps(payload)}\n\n"


@router.get("/events")
def events(once: bool = False, current_user: User = Depends(get_current_user)) -> StreamingResponse:
    event_bus = get_event_bus()
    channel = event_bus.subscribe(current_user.id)

    def stream() -> Generator[str, None, None]:
        try:
            yield _sse_encode(event_name="connected", payload={"user_id": current_user.id})
            if once:
                event = event_bus.poll(channel, timeout=1.0)
                if event is None:
                    yield _sse_encode(event_name="ping", payload={"ts": int(time.time())})
                else:
                    yield _sse_encode(event_name="message", payload=event)
                return
            while True:
                event = event_bus.poll(channel, timeout=1.0)
                if event is None:
                    yield _sse_encode(event_name="ping", payload={"ts": int(time.time())})
                    continue
                yield _sse_encode(event_name="message", payload=event)
        finally:
            event_bus.unsubscribe(current_user.id, channel)

    return StreamingResponse(stream(), media_type="text/event-stream")
