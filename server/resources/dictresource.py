"""
JsonResource and JsonCollection together offer a generic data storage mechanism
for data classes backed by JSON files. They offer commonly used operations like
create, save, delete, and find.

Functionality at the instance and collection levels are split logically between
the two classes. For example, JsonResource contains the method for saving an
instance, and JsonCollection has the methods for find specified items.

Usage is perhaps best illustrated with an example. Below, we define a simple
dataclass called DummyModel. As the name suggests, this serves as a model or
schema for dummy objects, but we will not interact with this class directly.
Instead, we declare an instance of a JsonCollection called Dummy, which can be
used to create new objects find objects in storage.

    from dataclasses import field
    from marshmallow_dataclass import dataclass

    @dataclass
    class DummyModel(JsonResource):
        id:     int = field(default=None)
        name:   str = field(default=None)

    Dummy = JsonCollection(DummyModel, "dummy")

    item = Dummy(id=0, name="foobar")
    item.save()

    results = Dummy.find(name="foobar")
"""

import os
import shutil
import uuid

from server.resources.abstractresource import AbstractResource, AbstractCollection
from server.resources.filter import Filter


class DictResource(AbstractResource):
    def delete(self):
        shutil.rmtree(self._storage_dir, ignore_errors=True)

    def get_dir(self):
        """
        Returns the path to the resource's data directory.

        This directory contains any additional files associated with the
        resource.
        """
        return self._storage_dir

    def on_ready(self):
        """
        Called after object is initalized and self.id is set.

        This can be used by subclasses to perform post-init setup such as
        creating subresources.
        """
        pass


class DictCollection(AbstractCollection):
    def __init__(self, resource_class, collection_name, id_type="numeric", parent=None):
        """
        Create a new collection.

        resource_class: class for the elements of the collection, must be
                        subclass of DictResource
        collection_name: name used for the collection directory
        id_type: type of ID for elements, either "numeric" or "uuid"
        parent: either None or an instance of JsonResource, in which case the
                collection will be stored in a subdirectory of that resource
        """
        if id_type not in ["uuid", "numeric"]:
            raise Exception("ID type {} is not supported".format(id_type))

        self.resource_class = resource_class
        self.collection_name = collection_name
        self.id_type = id_type
        self.parent = parent

        if parent is None:
            self.base_directory = os.path.join(DictCollection.data_directory, self.collection_name)
        elif isinstance(parent, AbstractResource):
            self.base_directory = os.path.join(parent._storage_dir, self.collection_name)
        else:
            raise Exception("Parent of type {} is not supported".format(type(parent)))

        # Used for auto-incrementing numeric IDs.
        self.next_id = 0

    def add(self, id):
        """
        Create a resource with a given ID.
        """
        path = os.path.join(self.base_directory, self.format_id(id))
        os.makedirs(path, exist_ok=True)
        item = self.resource_class(id)
        return self.prepare_item(item)

    def clear(self):
        """
        Delete all data belonging to this collection.
        """
        shutil.rmtree(self.base_directory, ignore_errors=True)

    def find(self, filt=None, **kwargs):
        """
        Find all objects that match the query parameters.
        """
        if not os.path.isdir(self.base_directory):
            return []

        if filt is None:
            filt = Filter()
            filt.add_from_dict(kwargs)

        results = []
        for dname in os.listdir(self.base_directory):
            subdir = os.path.join(self.base_directory, dname)
            if not os.path.isdir(subdir):
                continue
            item = self.resource_class(dname)
            self.prepare_item(item)
            if filt.matches(item):
                results.append(item)

        return results

    def find_by_id(self, id):
        """
        Find a specific object by id.

        Returns None if not found.
        """
        path = os.path.join(self.base_directory, self.format_id(id))
        if os.path.isdir(path):
            item = self.resource_class(id)
            item.id = id
            return self.prepare_item(item)
        else:
            return None

    def format_id(self, id):
        if self.id_type == "uuid":
            return str(id)

        else:
            return "{:08x}".format(id)

    def get_next_id(self):
        if self.id_type == "uuid":
            return str(uuid.uuid4())

        else:
            next_id = self.next_id

            if next_id == 0:
                items = self.find()
                if len(items) > 0:
                    next_id = max(item.id for item in items) + 1
                else:
                    next_id = 1

            self.next_id = next_id + 1
            return next_id

    def prepare_item(self, item):
        if item.id is None:
            item.id = self.get_next_id()
        item._collection = self
        item._storage_dir = os.path.join(self.base_directory, self.format_id(item.id))
        item.on_ready()
        return item
