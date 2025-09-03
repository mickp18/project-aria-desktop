import asyncio
from dataclasses import dataclass
from typing import Any, Dict, AsyncIterator

@dataclass
class Event:
    event_type: str
    payload: Any=None # optional data associated with event

class AsyncEventBus:
    def __init__(self):
        # Mapping of event topics to queues
        self._topics: Dict[str, asyncio.Queue] = {}

    def topic(self, event_type: str) -> asyncio.Queue:
        """Get or create a topic queue for a certain eventy type."""
        if event_type not in self._topics:              # create if not exists
            self._topics[event_type] = asyncio.Queue()  # new queue
        return self._topics[event_type]
    
    async def publish(self, event: Event)  -> None:
        """Publish an event to all subscribers of the event type."""
        queue = self.topic(event) # get the queue for this event type
        await queue.put(event)    # put event in the queue

    async def subscribe(self, event_type: str) -> AsyncIterator[Event]:
        """Subscribe to events of a given type (async generator)."""
        queue = self.topic(event_type)
        while True:
            event = await queue.get()
            yield event       # yield event to subscriber 
            queue.task_done() # mark event as processed