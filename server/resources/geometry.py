import numpy as np
import quaternion

from dataclasses import field
from marshmallow_dataclass import dataclass
from sqlalchemy.ext.mutable import MutableComposite


deg2rad = np.pi / 180


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

    def __add__(self, other):
        return Vector3f(self.x + other.x, self.y + other.y, self.z + other.z)

    def __neg__(self):
        return Vector3f(-float(self.x), -float(self.y), -float(self.z))

    def __sub__(self, other):
        return Vector3f(self.x - float(other.x), self.y - float(other.y), self.z - float(other.z))

    def totuple(self):
        return (self.x, self.y, self.z)

    def as_array(self):
        return np.array([self.x, self.y, self.z])

    def as_quaternion(self):
        return quaternion.from_euler_angles(deg2rad * self.z, deg2rad * self.y, deg2rad * self.x)


@dataclass
class Vector4f(MutableCompositeBase):
    x: float = field(default=0.0)
    y: float = field(default=0.0)
    z: float = field(default=0.0)
    w: float = field(default=0.0)

    def totuple(self):
        return (self.x, self.y, self.z, self.w)

    def apply_rotation(self, rotation):
        q1 = rotation.as_quaternion()
        q2 = self.as_quaternion()
        q = q1 * q2
        return Vector4f(q.x, q.y, q.z, q.w)

    def as_array(self):
        return np.array([self.x, self.y, self.z, self.w])

    def as_quaternion(self):
        return np.quaternion(self.w, self.x, self.y, self.z)

    def as_rotation_matrix(self):
        return quaternion.as_rotation_matrix(self.as_quaternion())

    @classmethod
    def from_quaternion(cls, q):
        return Vector4f(q.x, q.y, q.z, q.w)
