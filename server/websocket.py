import argparse
import asyncio
import json
import shlex
import sys
import time

from quart import g

from server.headset.routes import _update_headset
from server.utils.utils import GenericJsonEncoder


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        """
        Override ArgumentParser error method.

        The default implementation calls sys.exit on error,
        which would terminate the server!

        The Python 3.9 implementation adds an option to disable
        that functionality, but we may be running on Python 3.8.
        """
        raise Exception(message)


class WebsocketConnection:
    """
    Simplified object representing a websocket connection.

    Quart does something very interesting in the handler for the websocket
    connection. It does not give us an ordinary object but rather a werkzeug
    LocalProxy that looks like an object with methods (send, receive, close,
    etc.).  However, the dot opererator on the local proxy only works inside
    the context of a websocket request handler. This simple class is meant
    to unpack the useful methods from the local proxy and make them available
    outside that original context. For example, when handling a headset's
    PATCH request, we may need to notify other headsets over websocket.
    """
    def __init__(self, websocket_local_proxy):
        self.close = websocket_local_proxy.close
        self.receive = websocket_local_proxy.receive
        self.send = websocket_local_proxy.send


class WebsocketHandler:
    """
    Handler for a websocket connection.

    Whenever a new websocket connection is accepted, we create a
    WebsocketHandler instance and call the listen method in an asyncio task.
    The listen method waits for messages from the client and takes appropriate
    action. For example, if the client sends a subscribe command, the
    WebsocketHandler forwards this to the event dispatcher.
    """
    def __init__(self, dispatcher, websocket, subprotocol="json", user_id=None, close_after_seconds=60):
        self.dispatcher = dispatcher
        self.websocket = websocket
        self.subprotocol = subprotocol

        # Maintain a list of active subscriptions so that we can clean up
        # when the connection closes.
        self.subscriptions = set()

        # Track last successful send to detect repeated failures.
        self.last_successful_send = time.time()

        self.echo_own_events = True
        self.user_id = user_id
        self.close_after_seconds = close_after_seconds

        self.parser = WebsocketHandler.build_command_parser()

        self.running = True

    async def _send_event_notification(self, event, uri, *args, **kwargs):
        # Potentially suppress events that were generated by the same user's
        # actions.  For example, if a headset creates a feature through a POST
        # request, we do not need to send a notification to the same user's
        # websocket connection. This makes sense for headsets, not so much for
        # browser sessions, since a user could have multiple browser sessions
        # open.  Hence, the default is echoing enabled, and the websocket
        # client needs to request echoing be turned off.
        if not self.echo_own_events and g.user_id == self.user_id:
            return

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

        now = time.time()

        try:
            await self.websocket.send(payload)
            self.last_successful_send = now
        except:
            if now - self.last_successful_send > self.close_after_seconds:
                print("WS [{}]: closing connection after repeated send failures".format(self.user_id))
                await self.websocket.close()
                self.remove_subscriptions()
                self.running = False

    def remove_subscriptions(self):
        for event, uri_filter in self.subscriptions:
            self.dispatcher.remove_event_listener(event, uri_filter, self._send_event_notification)

    async def handle_message(self, message):
        try:
            args = self.parser.parse_args(shlex.split(message))
        except Exception as err:
            print("WS [{}]: error parsing command from client: {}".format(self.user_id, err))
            return

        if args.command == "subscribe":
            # Disallow duplicate subscriptions.
            # If the client subscribes multiple times, it is probably a bug.
            if (args.event, args.uri_filter) not in self.subscriptions:
                print("WS [{}]: subscribe {} {}".format(self.user_id, args.event, args.uri_filter))
                self.dispatcher.add_event_listener(args.event, args.uri_filter, self._send_event_notification)
                self.subscriptions.add((args.event, args.uri_filter))

        elif args.command == "unsubscribe":
            if (args.event, args.uri_filter) in self.subscriptions:
                print("WS [{}]: unsubscribe {} {}".format(self.user_id, args.event, args.uri_filter))
                self.dispatcher.remove_event_listener(args.event, args.uri_filter, self._send_event_notification)
                self.subscriptions.remove((args.event, args.uri_filter))

        elif args.command == "echo":
            if args.enabled == "off":
                self.echo_own_events = False
            else:
                self.echo_own_events = True

        # deprecated: users should replace with "echo [on|off]"
        elif args.command == "suppress":
            if args.enabled == "on":
                self.echo_own_events = False
            else:
                self.echo_own_events = True

        elif args.command == "move":
            if self.user_id is not None:
                patch = {
                    "position": dict(zip(["x", "y", "z"], args.position)),
                    "orientation": dict(zip(["x", "y", "z", "w"], args.orientation))
                }
                await _update_headset(self.user_id, patch)

        elif args.command == "exit":
            sys.exit(0)

        elif args.command == "user":
            self.user_id = args.id

    async def listen(self):
        try:
            while self.running:
                data = await self.websocket.receive()
                await self.handle_message(data)

        except asyncio.CancelledError:
            print("WS [{}]: connection closed, removing {} subscriptions".format(self.user_id, len(self.subscriptions)))
            self.remove_subscriptions()

            # Quart documentation warns that the cancellation error needs to be re-raised.
            # https://pgjones.gitlab.io/quart/how_to_guides/websockets.html
            raise

    @classmethod
    def build_command_parser(cls):
        description = """
        The websocket server supports various commands from the client much
        like a command-line interface. Each command should be sent as a single
        line message beginning with a command name and followed by arguments
        separated by spaces.

        The next section provides an overview of the supported commands, and
        the following section provides more detailed usage information for each
        command.
        """
        parser = ArgumentParser(
                prog="",
                description=description,
                add_help=False,
                formatter_class=argparse.RawTextHelpFormatter
        )

        command = parser.add_subparsers(dest="command", help="Command description")
        subscribe = command.add_parser("subscribe", help="Subscribe to an event type", add_help=False)
        unsubscribe = command.add_parser("unsubscribe", help="Unsubscribe from an event type", add_help=False)
        echo = command.add_parser("echo", help="Enable or disable echoing of user events", add_help=False)
        suppress = command.add_parser("suppress", help="(deprecated) use echo [on|off] instead", add_help=False)
        move = command.add_parser("move", help="Change headset pose", add_help=False)

        subscribe.add_argument("event", type=str)
        subscribe.add_argument("uri_filter", type=str, nargs="?", default="*")

        unsubscribe.add_argument("event", type=str)
        unsubscribe.add_argument("uri_filter", type=str, nargs="?", default="*")

        echo.add_argument("enabled", type=str, choices=["on", "off"])

        suppress.add_argument("enabled", type=str, choices=["on", "off"])

        move.add_argument("position", type=float, nargs=3, metavar="x")
        move.add_argument("orientation", type=float, nargs=4, metavar="w")

        command_usage_strings = [
            "command usage:\n",
            subscribe.format_usage()[7:],
            unsubscribe.format_usage()[7:],
            echo.format_usage()[7:],
            suppress.format_usage()[7:],
            move.format_usage()[7:]
        ]

        # These commands are useful for testing but must not be available in
        # production environment because of their security risks.
        if not g.environment.startswith("prod"):
            exit = command.add_parser("exit", help="Stop the server", add_help=False)
            user = command.add_parser("user", help="Set user ID for the connection", add_help=False)

            user.add_argument("id", type=str)

            command_usage_strings.extend([
                exit.format_usage()[7:],
                user.format_usage()[7:]
            ])

        parser.epilog = "".join(command_usage_strings)

        return parser


if __name__ == "__main__":
    parser = WebsocketHandler.build_command_parser()
    parser.print_help()
