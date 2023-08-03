from dataclasses import field
from marshmallow_dataclass import dataclass


@dataclass
class Box:
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
class Vector3f:
    x: float = field(default=0.0)
    y: float = field(default=0.0)
    z: float = field(default=0.0)

    def totuple(self):
        return (self.x, self.y, self.z)


@dataclass
class Vector4f:
    x: float = field(default=0.0)
    y: float = field(default=0.0)
    z: float = field(default=0.0)
    w: float = field(default=0.0)

    def totuple(self):
        return (self.x, self.y, self.z, self.w)
