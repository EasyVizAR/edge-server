import asyncio
import json
import textwrap

import quart.flask_patch # noqa

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin

from server.check_in import routes as check_ins
from server.feature import routes as features
from server.headset import routes as headsets
from server.incidents import routes as incidents
from server.layer import routes as layers
from server.location import routes as locations
from server.photo import routes as photos
from server.pose_changes import routes as pose_changes
from server.surface import routes as surfaces
from server.websocket import routes as websockets
from server import routes as other

from server.check_in.models import TrackingSession, CheckInSchema
from server.feature.models import MapMarker, FeatureSchema
from server.headset.models import MobileDevice, HeadsetSchema, RegisteredHeadsetSchema
from server.incidents.models import Incident, IncidentSchema
from server.layer.models import Layer, LayerSchema
from server.location.models import Location, LocationSchema
from server.photo.models import PhotoRecord, PhotoSchema
from server.pose_changes.models import DevicePose, PoseChangeSchema
from server.surface.models import Surface, SurfaceSchema

from server.websocket.connection import WebsocketHandler


async def create_openapi_spec(app):
    spec = APISpec(
        title="EasyVizAR Edge API",
        version="0.1",
        info=dict(
            description="Edge API"
        ),
        openapi_version="3.0",
        plugins=[
            FlaskPlugin(),
            MarshmallowPlugin(),
        ]
    )

    spec.components.schema("CheckIn", schema=CheckInSchema())
    spec.components.schema("Feature", schema=FeatureSchema())
    spec.components.schema("Headset", schema=HeadsetSchema())
    spec.components.schema("RegisteredHeadset", schema=RegisteredHeadsetSchema())
    spec.components.schema("Incident", schema=IncidentSchema())
    spec.components.schema("Layer", schema=LayerSchema())
    spec.components.schema("Location", schema=LocationSchema())
    spec.components.schema("Photo", schema=PhotoSchema())
    spec.components.schema("PoseChange", schema=PoseChangeSchema())
    spec.components.schema("Surface", schema=SurfaceSchema())

    spec.tag(dict(name="check-ins", description=TrackingSession.__doc__))
    spec.tag(dict(name="features", description=MapMarker.__doc__))
    spec.tag(dict(name="headsets", description=MobileDevice.__doc__))
    spec.tag(dict(name="incidents", description=Incident.__doc__))
    spec.tag(dict(name="layers", description=Layer.__doc__))
    spec.tag(dict(name="locations", description=Location.__doc__))
    spec.tag(dict(name="photos", description=PhotoRecord.__doc__))
    spec.tag(dict(name="pose-changes", description=DevicePose.__doc__))
    spec.tag(dict(name="surfaces", description=Surface.__doc__))

    # The websocket command parser has useful information about
    # the supported websocket client commands.
    parser = WebsocketHandler.build_command_parser()
    description = textwrap.indent(parser.format_help(), "    ")
    spec.tag(dict(name="websockets", description=description))

    async with app.test_request_context("/"):
        spec.path(view=check_ins.list_check_ins)
        spec.path(view=check_ins.create_check_in)

        spec.path(view=features.list_features)
        spec.path(view=features.create_feature)
        spec.path(view=features.delete_feature)
        spec.path(view=features.get_feature)
        spec.path(view=features.replace_feature)
        spec.path(view=features.update_feature)

        spec.path(view=headsets.list_headsets)
        spec.path(view=headsets.create_headset)
        spec.path(view=headsets.delete_headset)
        spec.path(view=headsets.get_headset)
        spec.path(view=headsets.replace_headset)
        spec.path(view=headsets.update_headset)
        spec.path(view=headsets.list_incident_headsets)

        spec.path(view=incidents.list_incidents)
        spec.path(view=incidents.create_incident)
        spec.path(view=incidents.delete_incident)
        spec.path(view=incidents.get_incident)
        spec.path(view=incidents.replace_incident)
        spec.path(view=incidents.update_incident)
        spec.path(view=incidents.get_active_incident)
        spec.path(view=incidents.change_active_incident)

        spec.path(view=layers.list_layers)
        spec.path(view=layers.create_layer)
        spec.path(view=layers.delete_layer)
        spec.path(view=layers.get_layer)
        spec.path(view=layers.replace_layer)
        spec.path(view=layers.update_layer)
        spec.path(view=layers.get_layer_file)
        spec.path(view=layers.upload_layer_image)

        spec.path(view=locations.list_locations)
        spec.path(view=locations.create_location)
        spec.path(view=locations.delete_location)
        spec.path(view=locations.get_location)
        spec.path(view=locations.replace_location)
        spec.path(view=locations.update_location)
        spec.path(view=locations.get_location_qrcode)
        spec.path(view=locations.get_location_model)
        spec.path(view=locations.get_location_route)

        spec.path(view=photos.list_photos)
        spec.path(view=photos.create_photo)
        spec.path(view=photos.delete_photo)
        spec.path(view=photos.get_photo)
        spec.path(view=photos.replace_photo)
        spec.path(view=photos.update_photo)
        spec.path(view=photos.get_photo_file)
        spec.path(view=photos.get_photo_file_by_name)
        spec.path(view=photos.get_photo_thumbnail)
        spec.path(view=photos.upload_photo_file)
        spec.path(view=photos.upload_photo_file_by_name)

        spec.path(view=pose_changes.list_pose_changes)
        spec.path(view=pose_changes.list_check_in_pose_changes)
        spec.path(view=pose_changes.create_pose_change)

        spec.path(view=surfaces.list_surfaces)
        spec.path(view=surfaces.clear_surfaces)
        spec.path(view=surfaces.delete_surface)
        spec.path(view=surfaces.get_surface)
        spec.path(view=surfaces.replace_surface)
        spec.path(view=surfaces.get_surface_file)
        spec.path(view=surfaces.upload_surface_file)

        spec.path(view=websockets.list_websockets)
        spec.path(view=websockets.delete_websocket)
        spec.path(view=websockets.ws)

    return spec


if __name__ == "__main__":
    from .main import app

    loop = asyncio.get_event_loop()
    spec = loop.run_until_complete(create_openapi_spec(app))

    print(spec.to_yaml())

    with open("docs/openapi.json", "w") as output:
        output.write(json.dumps(spec.to_dict()))
