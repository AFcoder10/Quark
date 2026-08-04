from __future__ import annotations

import asyncio

import pytest

from app.events.bus import Event, EventBus


class TestEventBus:
    def test_publish_sync(self):
        bus = EventBus()
        received = []
        bus.on("test", lambda event: received.append(event.name))
        bus.publish("test")
        assert len(received) == 1
        assert received[0] == "test"

    def test_publish_with_data(self):
        bus = EventBus()
        received = []
        bus.on("test", lambda event: received.append(event.data))
        bus.publish("test", foo="bar")
        assert received[0]["foo"] == "bar"

    def test_multiple_handlers(self):
        bus = EventBus()
        count = [0]
        bus.on("test", lambda event: count.__setitem__(0, count[0] + 1))
        bus.on("test", lambda event: count.__setitem__(0, count[0] + 1))
        bus.publish("test")
        assert count[0] == 2

    def test_on_any(self):
        bus = EventBus()
        received = []
        bus.on_any(lambda event: received.append(event.name))
        bus.publish("foo")
        bus.publish("bar")
        assert len(received) == 2

    def test_event_has_timestamp(self):
        bus = EventBus()
        received = []
        bus.on("test", lambda event: received.append(event))
        bus.publish("test")
        assert received[0].ts > 0

    def test_handler_exception_does_not_propagate(self):
        bus = EventBus()
        def bad_handler(event):
            raise ValueError("boom")
        bus.on("test", bad_handler)
        bus.publish("test")
        bus.publish("test")