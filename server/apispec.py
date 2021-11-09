import asyncio
import json

import quart.flask_patch

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin

from marshmallow import Schema, fields

from .main import app
from .maps import maps_routes
from .headset import headsetroutes


class VectorSchema(Schema):
    x = fields.Float(required = True)
    y = fields.Float(required = True)
    z = fields.Float(required = True)


class HeadsetSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    position = fields.Nested(VectorSchema())
    orientation = fields.Nested(VectorSchema())
    mapID = fields.Str()
    lastUpdate = fields.DateTime()


class HeadsetUpdateSchema(Schema):
    headsetID = fields.Str()
    position = fields.Nested(VectorSchema())
    orientation = fields.Nested(VectorSchema())
    mapID = fields.Str()


class MapSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    image = fields.Str()


class MapFeatureStyleSchema(Schema):
    placement = fields.Str()
    topOffset = fields.Float()
    leftOffset = fields.Float()
    icon = fields.Str()


class MapFeatureSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    position = fields.Nested(VectorSchema())
    mapID = fields.Str()
    style = fields.Nested(MapFeatureStyleSchema())


class ImageUploadSchema(Schema):
    id = fields.Str()
    url = fields.Str()
    intent = fields.Str()
    data = fields.Dict()
    type = fields.Str()


class SurfaceFileInformationSchema(Schema):
    id = fields.Str()
    filename = fields.Str()
    modified = fields.Float()
    size = fields.Integer()


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

headset_tag = {
    "name": "Headsets",
    "description": "Operations on Headset objects"
}

map_tag = {
    "name": "Maps",
    "description": "Operations on Map objects"
}

spec.components.schema("Headset", schema=HeadsetSchema)
spec.components.schema("HeadsetUpdate", schema=HeadsetUpdateSchema)
spec.components.schema("Map", schema=MapSchema)
spec.components.schema("MapFeature", schema=MapFeatureSchema)
spec.components.schema("ImageUpload", schema=ImageUploadSchema)
spec.components.schema("SurfaceFileInformation", schema=SurfaceFileInformationSchema)

async def add_routes_to_spec():
    async with app.test_request_context("/"):
        spec.path(view=headsetroutes.get_all)
        spec.path(view=headsetroutes.get)
        spec.path(view=headsetroutes.register)
        spec.path(view=headsetroutes.authenticate)
        spec.path(view=headsetroutes.update_position)

        spec.path(view=headsetroutes.image_upload)

        spec.path(view=maps_routes.list_maps)
        spec.path(view=maps_routes.show_map)
        spec.path(view=maps_routes.list_map_features)
        spec.path(view=maps_routes.add_map_feature)
        spec.path(view=maps_routes.create_map)


loop = asyncio.get_event_loop()
loop.run_until_complete(add_routes_to_spec())


if __name__ == "__main__":
    print(spec.to_yaml())

    with open("docs/openapi.json", "w") as output:
        output.write(json.dumps(spec.to_dict()))


