import os
from os.path import realpath

from dataclasses import field
from marshmallow_dataclass import dataclass

import pytest

from server.resources.csvresource import CsvCollection, CsvResource
from server.resources.jsonresource import JsonCollection, JsonResource



@dataclass
class ChildModel(CsvResource):
    x:      int = field(default=0)
    y:      int = field(default=0)
    z:      int = field(default=0)


@dataclass
class ParentModel(JsonResource):
    id:     int = field(default=None)
    name:   str = field(default=None)

    def on_ready(self):
        self.children = CsvCollection(ChildModel, "child", collection_name="children", parent=self)


@dataclass
class ContainerModel(CsvResource):
    position:       ChildModel = field(default_factory=ChildModel)
    orientation:    ChildModel = field(default_factory=ChildModel)


def test_csvresource():
    Dummy = CsvCollection(ChildModel, "dummy", collection_name="dummies")
    Dummy.clear()

    results = Dummy.find()
    assert results == []

    item = Dummy(x=1, y=2, z=3)
    Dummy.add(item)
    Dummy.add(item)
    Dummy.add(item)

    results = Dummy.find()
    assert len(results) == 3

    item = results[0]
    assert item.x == 1
    assert item.y == 2
    assert item.z == 3

    assert realpath(Dummy.storage_path) == realpath("data/dummies/dummies.csv")


def test_csvresource_parent():
    Parent = JsonCollection(ParentModel, "parent", collection_name="parents")
    Parent.clear()

    parent = Parent(name="parent")
    parent.save()

    child = parent.children(x=1, y=2, z=3)
    parent.children.add(child)
    parent.children.add(child)
    parent.children.add(child)

    results = parent.children.find()
    assert len(results) == 3

    assert realpath(parent.children.storage_path) == realpath("data/parents/00000001/children/children.csv")


def test_csvresource_nested():
    Dummy = CsvCollection(ContainerModel, "dummy", collection_name="dummies")
    Dummy.clear()

    item = Dummy(ChildModel(1,2,3), ChildModel(1,0,0))
    Dummy.add(item)

    results = Dummy.find()
    assert len(results) == 1

    item = results[0]
    assert item.position.x == 1
    assert item.position.y == 2
    assert item.position.z == 3
    assert item.orientation.x == 1
    assert item.orientation.y == 0
    assert item.orientation.z == 0
