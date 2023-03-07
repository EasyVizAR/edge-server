import asyncio
import json

from server.utils.utils import GenericJsonEncoder


class WebsocketHandler:
    """
    Handler for a websocket connection.

    Whenever a new websocket connection is accepted, we create a
    WebsocketHandler instance and call the listen method in an asyncio task.
    The listen method waits for messages from the client and takes appropriate
    action. For example, if the client sends a subscribe command, the
    WebsocketHandler forwards this to the event dispatcher.
    """
    def __init__(self, dispatcher, websocket_receive, websocket_send, subprotocol="json"):
        self.dispatcher = dispatcher
        self.websocket_receive = websocket_receive
        self.websocket_send = websocket_send
        self.subprotocol = subprotocol

        # Maintain a list of active subscriptions so that we can clean up
        # when the connection closes.
        self.subscriptions = set()

    async def _send_event_notification(self, event, uri, *args, **kwargs):
        obj = kwargs

        # For "json" protocol, include event information in the JSON-encoded object.
        if self.subprotocol == "json":
            obj['event'] = event
            obj['uri'] = uri

        body = json.dumps(obj, cls=GenericJsonEncoder)

        # For "json-with-header", the event information appears before the
        # JSON-encoded object.  This gives the receiver a chance to decide how
        # to deserialize the message body.
        if self.subprotocol == "json-with-header":
            payload = "{} {} ".format(event, uri) + body
        else:
            payload = body

        await self.websocket_send(payload)

    async def listen(self):
        try:
            while True:
                data = await self.websocket_receive()

                words = data.split()
                if len(words) < 2:
                    print("WS: malformed data from client ({})".format(data))
                    continue

                command = words[0]
                event = words[1]
                uri_filter = words[2] if len(words) > 2 else "*"

                if command == "subscribe":
                    # Disallow duplicate subscriptions.
                    # If the client subscribes multiple times, it is probably a bug.
                    if (event, uri_filter) not in self.subscriptions:
                        print("WS: subscribe {} {}".format(event, uri_filter))
                        self.dispatcher.add_event_listener(event, uri_filter, self._send_event_notification)
                        self.subscriptions.add((event, uri_filter))

                elif command == "unsubscribe":
                    if (event, uri_filter) in self.subscriptions:
                        print("WS: unsubscribe {} {}".format(event, uri_filter))
                        self.dispatcher.remove_event_listener(event, uri_filter, self._send_event_notification)
                        self.subscriptions.remove((event, uri_filter))

                else:
                    print("WS: unexpected command {} from client".format(command))

        except asyncio.CancelledError:
            print("Websocket connection closed, removing {} subscriptions".format(len(self.subscriptions)))
            for event, uri_filter in self.subscriptions:
                self.dispatcher.remove_event_listener(event, uri_filter, self._send_event_notification)

            # Quart documentation warns that the cancellation error needs to be re-raised.
            # https://pgjones.gitlab.io/quart/how_to_guides/websockets.html
            raise
