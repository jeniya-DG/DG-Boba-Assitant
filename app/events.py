# events.py
import asyncio
from typing import Any, List

_subscribers: List[asyncio.Queue] = []

def publish(event: Any) -> None:
    for q in list(_subscribers):
        try:
            q.put_nowait(event)
        except Exception:
            pass

async def subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _subscribers.append(q)
    return q

def unsubscribe(q: asyncio.Queue) -> None:
    try:
        _subscribers.remove(q)
    except ValueError:
        pass
