from dataclasses import field
from marshmallow_dataclass import dataclass


@dataclass
class Box:
    left:   float = field(default=0.0)
    top:    float = field(default=0.0)
    width:  float = field(default=0.0)
    height: float = field(default=0.0)


@dataclass
class Vector3f:
    x: float = field(default=0.0)
    y: float = field(default=0.0)
    z: float = field(default=0.0)


@dataclass
class Vector4f:
    x: float = field(default=0.0)
    y: float = field(default=0.0)
    z: float = field(default=0.0)
    w: float = field(default=0.0)
