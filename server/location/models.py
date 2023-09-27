import datetime
import time
import uuid

from marshmallow import post_dump
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemySchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from server.feature.models import FeatureModel
from server.layer.models import LayerModel
from server.scene.models import SceneModel
from server.surface.models import SurfaceModel
from server.resources.dataclasses import dataclass, field
from server.resources.db import Base, MigrationSchema
from server.resources.dictresource import DictCollection
from server.resources.jsonresource import JsonCollection, JsonResource


# DEPRECATED
@dataclass
class HeadsetConfiguration(JsonResource):
    enable_mesh_capture:    bool = field(default=True,
                                         description="Enable automatic capturing of environment surfaces for mapping")
    enable_photo_capture:   bool = field(default=False,
                                         description="Enable automatic capturing of high resolution photos")
    enable_extended_capture:   bool = field(default=False,
                                         description="Enable automatic capturing of photos, depth, geometry, and intensity images")


# DEPRECATED
@dataclass
class LocationModel(JsonResource):
    """
    A location such as a building with a definite geographical boundary.

    A location may have one or more features, which are points of interest,
    messages, or other pieces digital information that team members would like
    to share.

    A location may have one or more map layers, e.g. a floor plan for each
    floor of a building.
    """
    id:     str
    name:   str

    description: str = field(default=None,
                             description="Location description or notes to be displayed on the dashboard")

    model_path: str = field(default=None)
    model_url:  str = field(default=None)

    last_surface_update: float = field(default=0.0,
                                       description="Last time a surface was updated")

    headset_configuration: HeadsetConfiguration = field(default_factory=HeadsetConfiguration,
                                                        description="Application configuration that headsets receive when checking in")

    def on_ready(self):
        self.Feature = JsonCollection(FeatureModel, "feature", parent=self)
        self.Layer = JsonCollection(LayerModel, "layer", parent=self)
        self.Scene = DictCollection(SceneModel, "scenes", id_type="uuid", parent=self)
        self.Surface = JsonCollection(SurfaceModel, "surface", id_type="uuid", parent=self)


class DeviceConfiguration(Base):
    """
    A set of configuration values for a single device or for all devices in a
    given location.
    """
    __tablename__ = "device_configurations"
    __allow_update__ = set(['enable_mesh_capture', 'enable_photo_capture', 'enable_extended_capture'])

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    location_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("locations.id"), nullable=True)
    mobile_device_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("mobile_devices.id"), nullable=True)

    enable_mesh_capture: Mapped[bool] = mapped_column(default=True)
    enable_photo_capture: Mapped[bool] = mapped_column(default=False)
    enable_extended_capture: Mapped[bool] = mapped_column(default=False)

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)


class Location(Base):
    """
    A location such as a building with a definite geographical boundary.

    A location may have one or more map markers, which are points of interest,
    messages, or other pieces digital information that team members would like
    to share.

    A location may have one or more map layers, e.g. a floor plan for each
    floor of a building.
    """
    __tablename__ = "locations"
    __allow_update__ = set(['name', 'description'])

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(default="New Location")
    description: Mapped[str] = mapped_column(default="")

    created_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    device_configuration: Mapped[DeviceConfiguration] = relationship(cascade="all, delete-orphan", uselist=False)


class DeviceConfigurationSchema(SQLAlchemySchema):
    class Meta:
        model = DeviceConfiguration
        load_instance = True

    enable_mesh_capture = auto_field(description="Enable automatic capturing of environment surfaces for mapping")
    enable_photo_capture = auto_field(description="Enable automatic capturing of high resolution photos")
    enable_extended_capture = auto_field(description="Enable automatic capturing of photos, depth, geometry, and intensity images")


class LocationSchema(MigrationSchema):
    __convert_isotime_fields__ = ['created_time', 'updated_time']

    class Meta:
        model = Location
        load_instance = True

    id = auto_field(description="Location ID (UUID)")

    name = auto_field(description="Location name")
    description = auto_field(description="Location description")

    created_time = auto_field(description="Time the location was created")
    updated_time = auto_field(description="Last time the location was updated")

    #device_configuration = Nested(DeviceConfigurationSchema, many=False)

    @post_dump(pass_original=True)
    def add_headset_configuration(self, data, original, **kwargs):
        if original.has('device_configuration'):
            schema = DeviceConfigurationSchema()
            data['headset_configuration'] = schema.dump(original.device_configuration)
        return data
