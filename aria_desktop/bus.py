import asyncio
from dataclasses import dataclass
from typing import Any, Dict, AsyncIterator, Optional


@dataclass
class Event:
    event_type: str
    payload: Any=None # optional data associated with event

class AsyncEventBus:
    def __init__(self):
        # Mapping of event topics to queues
        self._topics: Dict[str, asyncio.Queue] = {}
        self._latest: Dict[str, Event] = {}  # Store latest event
        self._notifiers: Dict[str, asyncio.Event] = {}  # Signal new data

    def topic(self, event_type: str, maxsize: int = 0) -> asyncio.Queue:
        """Get or create a topic queue for a certain event type."""
        if event_type not in self._topics:
            self._topics[event_type] = asyncio.Queue(maxsize=maxsize)
        return self._topics[event_type]
    
    async def publish(self, event: Event) -> None:
        """Publish an event - for video frames, just store the latest."""
        if event.event_type == "rgb_frame":
            # For video frames, use latest-only pattern
            self._latest[event.event_type] = event
            
            # Create notifier if doesn't exist
            if event.event_type not in self._notifiers:
                self._notifiers[event.event_type] = asyncio.Event()
            
            # Signal that new data is available
            self._notifiers[event.event_type].set()
        else:
            # For other events, use queue
            queue = self.topic(event.event_type)
            await queue.put(event)

    async def subscribe(self, event_type: str, latest_only: bool = False) -> AsyncIterator[Event]:
        """
        Subscribe to events of a given type.
        If latest_only=True, always get the most recent frame (no queue).
        """
        if latest_only or event_type == "rgb_frame":
            # Latest-only pattern for video frames
            if event_type not in self._notifiers:
                self._notifiers[event_type] = asyncio.Event()
            
            notifier = self._notifiers[event_type]
            
            while True:
                await notifier.wait()  # Wait for new data
                notifier.clear()  # Reset the notifier
                
                if event_type in self._latest:
                    event = self._latest[event_type]
                    yield event
        else:
            # Queue pattern for other events
            queue = self.topic(event_type)
            while True:
                event = await queue.get()
                yield event
                queue.task_done()