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

import json
import os
import shutil
import time
import uuid


class JsonResource:
    def delete(self):
        shutil.rmtree(self._storage_dir, ignore_errors=True)

    def get_dir(self):
        """
        Returns the path to the resource's data directory.

        This directory contains the resource's JSON object file and any other
        files the resource may generate.
        """
        return self._storage_dir

    def get_path(self):
        """
        Returns the path to the resource's JSON object file.
        """
        return self._storage_path

    def matches(self, query):
        for k, v in query.items():
            if v is not None and getattr(self, k) != v:
                return False
        return True

    def notify_listeners(self, listeners):
        remaining = []
        for future, query in listeners:
            if future.cancelled():
                continue
            elif self.matches(query):
                future.set_result(self)
            else:
                remaining.append((future, query))

        listeners.clear()
        listeners.extend(remaining)

    def on_ready(self):
        """
        Called after object is initalized and self.id is set.

        This can be used by subclasses to perform post-init setup such as
        creating subresources.
        """
        pass

    def save(self):
        os.makedirs(self._storage_dir, exist_ok=True)

        # Check if this is a new object.
        created = not os.path.exists(self._storage_path)

        self.updated = time.time()

        with open(self._storage_path, 'w') as output:
            json_out = self.Schema().dumps(self)
            output.write(json_out)

        # Notify any listeners of the change.
#        if created:
#            self.notify_listeners(self.on_create)
#        self.notify_listeners(self.on_update)

        return created


class JsonCollection:
    data_directory = "data"

    on_create = []
    on_update = []

    def __init__(self, resource_class, resource_name, collection_name=None, id_type="numeric", parent=None):
        """
        Create a new collection.

        resource_class: class for the elements of the collection, must be
                        subclass of JsonResource
        resource_name: description name for the resource type which will be
                       used in the resource filename, e.g. "headset"
        collection_name: name used for the collection directory; if None, the
                         default will be resource_name+"s", e.g. "headsets"
        id_type: type of ID for elements, either "numeric" or "uuid"
        parent: either None or an instance of JsonResource, in which case the
                collection will be stored in a subdirectory of that resource
        """
        if not issubclass(resource_class, JsonResource):
            raise Exception("{} is not a subclass of JsonResource".format(resource_class))

        if id_type not in ["uuid", "numeric"]:
            raise Exception("ID type {} is not supported".format(id_type))

        self.resource_class = resource_class
        self.resource_name = resource_name
        self.id_type = id_type
        self.parent = parent

        if collection_name is None:
            self.collection_name = resource_name + "s"
        else:
            self.collection_name = collection_name

        if parent is None:
            self.base_directory = os.path.join(JsonCollection.data_directory, self.collection_name)
        elif isinstance(parent, JsonResource):
            self.base_directory = os.path.join(parent._storage_dir, self.collection_name)
        else:
            raise Exception("Parent of type {} is not supported".format(type(parent)))

        self.resource_filename = "{}.json".format(self.resource_name)
        self.resource_schema = resource_class.Schema()

        # Used for auto-incrementing numeric IDs.
        self.next_id = 0

    def __call__(self, *args, **kwargs):
        """
        Construct a new instance of the underlying resource class.

        This allows treating the collection object as if it were a class.
        """
        item = self.resource_class(*args, **kwargs)
        if item.id is None:
            item.id = self.get_next_id()
        item._collection = self
        item._storage_dir = os.path.join(self.base_directory, self.format_id(item.id))
        item._storage_path = os.path.join(self.base_directory, self.format_id(item.id), self.resource_filename)
        item.on_ready()
        return item

    def clear(self):
        """
        Delete all data belonging to this collection.
        """
        shutil.rmtree(self.base_directory, ignore_errors=True)

    def find(self, **kwargs):
        """
        Find all objects that match the query parameters.
        """
        if not os.path.isdir(self.base_directory):
            return []

        results = []
        for dname in os.listdir(self.base_directory):
            subdir = os.path.join(self.base_directory, dname)
            if not os.path.isdir(subdir):
                continue
            fname = os.path.join(subdir, self.resource_filename)
            with open(fname, "r") as source:
                item = self.resource_schema.loads(source.read())
                if item.matches(kwargs):
                    results.append(item)

        return results

    def find_by_id(self, id):
        """
        Find a specific object by id.

        Returns None if not found.
        """
        path = os.path.join(self.base_directory, self.format_id(id), self.resource_filename)
        try:
            with open(path, "r") as source:
                return self.resource_schema.loads(source.read())
        except:
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
