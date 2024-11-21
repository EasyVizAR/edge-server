import numpy as np
import quaternion

from dataclasses import field
from marshmallow_dataclass import dataclass
from sqlalchemy.ext.mutable import MutableComposite


class MutableCompositeBase(MutableComposite):
    def __setattr__(self, key, value):
        """Intercept set events"""

        # set the attribute
        object.__setattr__(self, key, value)

        # alert all parents to the change
        self.changed()


@dataclass
class Box(MutableCompositeBase):
    left:   float = field(default=0.0)
    top:    float = field(default=0.0)
    width:  float = field(default=0.0)
    height: float = field(default=0.0)

    def get(self, attr, default=None):
        if hasattr(self, attr):
            return getattr(self, attr)
        else:
            return default


@dataclass
class Vector3f(MutableCompositeBase):
    x: float = field(default=0.0)
    y: float = field(default=0.0)
    z: float = field(default=0.0)

    def totuple(self):
        return (self.x, self.y, self.z)

    def as_array(self):
        return np.array([self.x, self.y, self.z])


@dataclass
class Vector4f(MutableCompositeBase):
    x: float = field(default=0.0)
    y: float = field(default=0.0)
    z: float = field(default=0.0)
    w: float = field(default=0.0)

    def totuple(self):
        return (self.x, self.y, self.z, self.w)

    def as_array(self):
        return np.array([self.x, self.y, self.z, self.w])

    def as_quaternion(self):
        return np.quaternion(self.w, self.x, self.y, self.z)

    def as_rotation_matrix(self):
        return quaternion.as_rotation_matrix(self.as_quaternion())
