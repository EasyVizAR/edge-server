import asyncio
import json

import quart.flask_patch

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin

from marshmallow import Schema, fields

from server.annotation import routes as annotations
from server.feature import routes as features
from server.headset import routes as headsets
from server.incidents import routes as incidents
from server.layer import routes as layers
from server.location import routes as locations
from server.photo import routes as photos
from server.pose_changes import routes as pose_changes
from server.scene import routes as scenes
from server.surface import routes as surfaces
from server import routes as other

from server.annotation.models import AnnotationModel
from server.feature.models import FeatureModel
from server.headset.models import HeadsetModel, RegisteredHeadsetModel
from server.incidents.models import IncidentModel
from server.layer.models import LayerModel
from server.location.models import LocationModel
from server.photo.models import PhotoModel
from server.pose_changes.models import PoseChangeModel
from server.scene.models import SceneDescriptor, SceneModel
from server.surface.models import SurfaceModel


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

    spec.components.schema("Annotation", schema=AnnotationModel.Schema())
    spec.components.schema("Feature", schema=FeatureModel.Schema())
    spec.components.schema("Headset", schema=HeadsetModel.Schema())
    spec.components.schema("RegisteredHeadset", schema=RegisteredHeadsetModel.Schema())
    spec.components.schema("Incident", schema=IncidentModel.Schema())
    spec.components.schema("Layer", schema=LayerModel.Schema())
    spec.components.schema("Location", schema=LocationModel.Schema())
    spec.components.schema("Photo", schema=PhotoModel.Schema())
    spec.components.schema("PoseChange", schema=PoseChangeModel.Schema())
    spec.components.schema("SceneDescriptor", schema=SceneDescriptor.Schema())
    spec.components.schema("Surface", schema=SurfaceModel.Schema())

    spec.tag(dict(name="annotations", description=AnnotationModel.__doc__))
    spec.tag(dict(name="features", description=FeatureModel.__doc__))
    spec.tag(dict(name="headsets", description=HeadsetModel.__doc__))
    spec.tag(dict(name="incidents", description=IncidentModel.__doc__))
    spec.tag(dict(name="layers", description=LayerModel.__doc__))
    spec.tag(dict(name="locations", description=LocationModel.__doc__))
    spec.tag(dict(name="photos", description=PhotoModel.__doc__))
    spec.tag(dict(name="pose-changes", description=PoseChangeModel.__doc__))
    spec.tag(dict(name="scenes", description=SceneModel.__doc__))
    spec.tag(dict(name="surfaces", description=SurfaceModel.__doc__))

    async with app.test_request_context("/"):
        spec.path(view=annotations.list_annotations)
        spec.path(view=annotations.create_annotation)
        spec.path(view=annotations.delete_annotation)
        spec.path(view=annotations.get_annotation)
        spec.path(view=annotations.replace_annotation)
        spec.path(view=annotations.update_annotation)

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
        spec.path(view=photos.upload_photo_file)

        spec.path(view=pose_changes.list_pose_changes)
        spec.path(view=pose_changes.create_pose_change)

        spec.path(view=scenes.list_scenes)
        spec.path(view=scenes.get_scene)
        spec.path(view=scenes.replace_scene)

        spec.path(view=surfaces.list_surfaces)
        spec.path(view=surfaces.create_surface)
        spec.path(view=surfaces.delete_surface)
        spec.path(view=surfaces.get_surface)
        spec.path(view=surfaces.replace_surface)
        spec.path(view=surfaces.update_surface)
        spec.path(view=surfaces.get_surface_file)
        spec.path(view=surfaces.upload_surface_file)

        spec.path(view=other.ws)

    return spec


if __name__ == "__main__":
    from .main import app

    loop = asyncio.get_event_loop()
    spec = loop.run_until_complete(create_openapi_spec(app))

    print(spec.to_yaml())

    with open("docs/openapi.json", "w") as output:
        output.write(json.dumps(spec.to_dict()))
