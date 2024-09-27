import json


from server.utils.utils import GenericJsonEncoder


class MessageSerializer:
    def serialize(self, event, uri, obj):
        raise NotImplemented

    def reduce_object(self, obj):
        if obj.get("current") is not None:
            return obj['current']
        elif obj.get("previous") is not None:
            return obj['previous']
        else:
            return obj


class JsonSerializer(MessageSerializer):
    def serialize(self, event, uri, obj):
        # For "json" protocol, include event information within the JSON-encoded object.
        obj['event'] = event
        obj['uri'] = uri

        return json.dumps(obj, cls=GenericJsonEncoder)


class JsonV2Serializer(MessageSerializer):
    def serialize(self, event, uri, obj):
        obj = self.reduce_object(obj)

        # For "json" protocol, include event information within the JSON-encoded object.
        obj['_meta'] = {
            "event": event,
            "uri": uri,
        }

        return json.dumps(obj, cls=GenericJsonEncoder)


class JsonWithHeaderSerializer(MessageSerializer):
    def serialize(self, event, uri, obj):
        # For "json-with-header", the event information appears before the
        # JSON-encoded object.  This gives the receiver a chance to decide how
        # to deserialize the message body.
        header = f"{event} {uri} "
        body = json.dumps(obj, cls=GenericJsonEncoder)

        return header + body


class JsonWithHeaderV2Serializer(MessageSerializer):
    def serialize(self, event, uri, obj):
        # For "json-with-header-v2", the event information appears before the
        # JSON-encoded object.  This gives the receiver a chance to decide how
        # to deserialize the message body.
        header = f"{event} {uri} "

        # This version attempts to simplify the communication by removing
        # the redundant previous/current objects.
        obj = self.reduce_object(obj)

        body = json.dumps(obj, cls=GenericJsonEncoder)

        return header + body


# Serializer for each WS subprotocol name
message_serializers = {
    "json": JsonSerializer(),
    "json-v2": JsonV2Serializer(),
    "json-with-header": JsonWithHeaderSerializer(),
    "json-with-header-v2": JsonWithHeaderV2Serializer(),
}
