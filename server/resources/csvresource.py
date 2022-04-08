"""
CsvResource and CsvCollection together offer a generic data storage mechanism
optimized for append-only data storage such as headset pose changes.

Functionality at the instance and collection levels are split logically between
the two classes. For example, CsvResource contains the method for saving an
instance, and CsvCollection has the methods for find specified items.

Usage is perhaps best illustrated with an example. Below, we define a simple
dataclass called DummyModel. As the name suggests, this serves as a model or
schema for dummy objects, but we will not interact with this class directly.
Instead, we declare an instance of a CsvCollection called Dummy, which can be
used to create new objects find objects in storage.

    from dataclasses import field
    from marshmallow_dataclass import dataclass

    @dataclass
    class DummyModel(CsvResource):
        x:  int = field(default=0)
        y:  int = field(default=0)
        z:  int = field(default=0)

    Dummy = CsvCollection(DummyModel, "dummy")

    item = Dummy(x=1, y=2, z=3)
    Dummy.add(item)

    results = Dummy.find()
"""

import csv
import dataclasses
import os
import shutil
import time

from .jsonresource import JsonResource


def repack(data):
    """
    Recreate a nested object structure from a flat dictionary.

    Example:
        repack({"p.x": 1}) -> {"p": {"x": 1}}
    """
    result = dict()

    for key, value in data.items():
        steps = key.split(".")

        pointer = result
        while len(steps) > 1:
            if steps[0] not in pointer:
                pointer[steps[0]] = dict()
            pointer = pointer[steps.pop(0)]
        pointer[steps[0]] = value

    return result


class CsvResource:
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
        Called after object is initalized.
        """
        pass

    def reload(self, data):
        """
        Recursively reconstruct this object and child objects from a dictionary.
        """
        for key, value in data.items():
            parts = key.split(".")

            tmp = self
            while len(parts) > 1:
                tmp = getattr(tmp, parts.pop(0))
            setattr(tmp, parts[0], value)

    def unpack(self, obj=None):
        """
        Recursively deconstruct this object into two flat lists of field names and field values.
        """
        if obj is None:
            obj = self

        field_names = []
        field_values = []

        for field in dataclasses.fields(obj):
            if dataclasses.is_dataclass(field.type):
                subnames, subvalues = self.unpack(getattr(obj, field.name))

                for name in subnames:
                    dotted_name = "{}.{}".format(field.name, name)
                    field_names.append(dotted_name)

                field_values.extend(subvalues)

            else:
                field_names.append(field.name)
                field_values.append(getattr(obj, field.name))

        return (field_names, field_values)


class CsvCollection:
    data_directory = "data"

    on_create = []
    on_update = []

    def __init__(self, resource_class, resource_name, collection_name=None, id_type="numeric", parent=None):
        """
        Create a new collection.

        resource_class: class for the elements of the collection, must be
                        subclass of CsvResource
        resource_name: description name for the resource type which will be
                       used in the resource filename, e.g. "headset"
        collection_name: name used for the collection directory; if None, the
                         default will be resource_name+"s", e.g. "headsets"
        id_type: type of ID for elements, either "numeric" or "uuid"
        parent: either None or an instance of JsonResource, in which case the
                collection will be stored in a subdirectory of that resource
        """
        if not issubclass(resource_class, CsvResource):
            raise Exception("{} is not a subclass of CsvResource".format(resource_class))

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
            self.base_directory = os.path.join(CsvCollection.data_directory, self.collection_name)
        elif isinstance(parent, JsonResource):
            self.base_directory = os.path.join(parent._storage_dir, self.collection_name)
        else:
            raise Exception("Parent of type {} is not supported".format(type(parent)))

        self.collection_filename = "{}.csv".format(self.collection_name)
        self.storage_path = os.path.join(self.base_directory, self.collection_filename)

        self.resource_schema = resource_class.Schema()

    def __call__(self, *args, **kwargs):
        """
        Construct a new instance of the underlying resource class.

        This allows treating the collection object as if it were a class.
        """
        item = self.resource_class(*args, **kwargs)
        item.on_ready()
        return item

    def add(self, obj):
        """
        Add an instance of resource_class.
        """
        if not isinstance(obj, self.resource_class):
            raise Exception("Type of object ({}) is not {}".format(type(obj), self.resource_class))

        # Make a directory for the collection even though it is a single file.
        # This may allow us to do paging later on for very large collections.
        os.makedirs(self.base_directory, exist_ok=True)

        created = not os.path.exists(self.storage_path)

        with open(self.storage_path, "a") as output:
            field_names, field_values = obj.unpack()

            writer = csv.writer(output)
            if created:
                writer.writerow(field_names)
            writer.writerow(field_values)

    def clear(self):
        """
        Delete all data belonging to this collection.
        """
        shutil.rmtree(self.base_directory, ignore_errors=True)

    def find(self, **kwargs):
        """
        Find all objects that match the query parameters.
        """
        if not os.path.exists(self.storage_path):
            return []

        results = []
        with open(self.storage_path, "r") as source:
            reader = csv.DictReader(source)
            for line in reader:
                line = repack(line)

                item = self.resource_schema.load(line)
                if item.matches(kwargs):
                    results.append(item)

        return results
