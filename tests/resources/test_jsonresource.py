import os
import time

from dataclasses import field
from marshmallow_dataclass import dataclass

import pytest

from server.resources.jsonresource import JsonCollection, JsonResource



@dataclass
class ChildModel(JsonResource):
    id:     int = field(default=None)
    name:   str = field(default=None)


@dataclass
class ParentModel(JsonResource):
    id:     int = field(default=None)
    name:   str = field(default=None)

    def on_ready(self):
        self.children = JsonCollection(ChildModel, "child", collection_name="children", parent=self)


def test_jsonresource():
    Dummy = JsonCollection(ChildModel, "dummy", collection_name="dummies")
    Dummy.clear()

    results = Dummy.find()
    assert results == []

    res1 = Dummy(0, "foo")
    created = res1.save()
    assert created is True
    assert res1.get_path() == "data/dummies/00000000/dummy.json"
    assert os.path.exists(res1.get_path())

    time.sleep(1) # make sure this item has a later modified time
    res2 = Dummy(name="foo")
    created = res2.save()
    assert created is True
    assert res2.id == 1

    res2.name = "bar"
    created = res2.save()
    assert created is False

    results = Dummy.find()
    assert len(results) == 2

    results = Dummy.find(name="foo")
    assert len(results) == 1
    assert results[0].id == 0

    results = Dummy.find(name="foo", id=None)
    assert len(results) == 1
    assert results[0].id == 0

    results = Dummy.find(name="foo", id=5)
    assert results == []

    result = Dummy.find_by_id(1)
    assert result.name == "bar"

    newest = Dummy.find_newest()
    assert newest is not None
    assert newest.id == res2.id

    res1.delete()
    assert not os.path.exists(res1.get_path())

    res2.delete()
    assert not os.path.exists(res2.get_path())

    Dummy.clear()
    assert len(Dummy.find()) == 0


def test_jsonresource_subcollection():
    Parent = JsonCollection(ParentModel, "parent", collection_name="parents")
    Parent.clear()

    parent = Parent(name="parent")
    parent.save()

    child1 = parent.children(name="child1")
    child1.save()

    time.sleep(1) # make sure this item has a later modified time
    child2 = parent.children(name="child2")
    child2.save()

    results = parent.children.find()
    assert len(results) == 2

    newest = parent.children.find_newest()
    assert newest is not None
    assert newest.name == "child2"

    assert child1.get_path() == "data/parents/00000001/children/00000001/child.json"
    assert child2.get_path() == "data/parents/00000001/children/00000002/child.json"
