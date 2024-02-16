import asyncio
import fnmatch

from collections import defaultdict


class EventDispatcher:
    """
    Async-friendly event dispatcher.

    EventDispatcher serves as a central point for managing event
    notifications.  It should generally be instantiated as a singleton,
    which multiple unrelated code modules might use to send events.

    Events are characterized by two strings, the event description, and
    a URI.  Event descriptions should be fixed strings easily understood
    by developers such as "headsets:created" and "headsets:updated",
    wherase the URI should encode a meaningful object hierarchy, for
    example "/locations/123/features".  When registering an event
    lister, we support wildcards in the URI filter, but not in the
    event description. This offers a good balance between efficiency
    and flexibility.

    The listener function should be prepared to accept two positional
    arguments, the event description and URI, as well as any variable
    event-specific arguments.

    The example below illustrates registering an event listener on
    various URI filters with and without wildcards. The listener
    function will be called three times as a result.

        dispatcher = EventDispatcher()

        def example_listener(event, uri, *args, **kwargs):
            pass

        dispatcher.add_event_listener("headsets:updated", "*", listener)
        dispatcher.add_event_listener("headsets:updated", "/headsets/*", listener)
        dispatcher.add_event_listener("headsets:updated", "/headsets/123", listener)

        dispatcher.dispatch_event("headsets:updated", "/headsets/123")
    """
    def __init__(self):
        self.events = defaultdict(list)

    def add_event_listener(self, event, uri_filter, listener):
        self.events[event].append((uri_filter, listener))

    def remove_event_listener(self, event, uri_filter, listener):
        try:
            self.events[event].remove((uri_filter, listener))
        except ValueError:
            pass

    async def wait_for(self, events, timeout=None):
        future = asyncio.get_event_loop().create_future()
        async def future_listener(*args, **kwargs):
            if not future.cancelled():
                future.set_result(True)

        for event, uri_filter in events:
            self.add_event_listener(event, uri_filter, future_listener)

        try:
            status = await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            status = False

        for event, uri_filter in events:
            self.remove_event_listener(event, uri_filter, future_listener)

        return status

    async def dispatch_event(self, event, uri, *args, **kwargs):
        for uri_filter, listener in self.events[event]:
            if fnmatch.fnmatch(uri, uri_filter):
                await listener(event, uri, *args, **kwargs)

