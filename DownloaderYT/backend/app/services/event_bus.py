from __future__ import annotations

from collections import defaultdict
from queue import Empty, Queue
from threading import Lock
from typing import Any


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[int, list[Queue[dict[str, Any]]]] = defaultdict(list)
        self._lock = Lock()

    def publish(self, user_id: int, event: dict[str, Any]) -> None:
        with self._lock:
            subscribers = list(self._subscribers.get(user_id, []))
        for queue in subscribers:
            queue.put(event)

    def subscribe(self, user_id: int) -> Queue[dict[str, Any]]:
        channel: Queue[dict[str, Any]] = Queue()
        with self._lock:
            self._subscribers[user_id].append(channel)
        return channel

    def unsubscribe(self, user_id: int, channel: Queue[dict[str, Any]]) -> None:
        with self._lock:
            listeners = self._subscribers.get(user_id, [])
            if channel in listeners:
                listeners.remove(channel)
            if not listeners and user_id in self._subscribers:
                del self._subscribers[user_id]

    @staticmethod
    def poll(channel: Queue[dict[str, Any]], timeout: float = 0.1) -> dict[str, Any] | None:
        try:
            return channel.get(timeout=timeout)
        except Empty:
            return None

