import asyncio
import os
import shutil
import time

from dataclasses import dataclass, field
from typing import ClassVar

from quart import current_app
from marshmallow_dataclass import dataclass


@dataclass
class WorkItem:
    id: int
    contentType: str    = field(default="image/jpeg")
    sourceType: str     = field(default="camera")
    fileUrl: str        = field(default=None)
    filePath: str       = field(default=None)
    retention: str      = field(default="auto")
    status: str         = field(default="created")
    created: float      = field(default_factory=time.time)
    updated: float      = field(default_factory=time.time)

    # Class variable used to cache next WorkItem ID
    next_id: ClassVar[int] = 0

    # Class variable for event listeners
    on_create: ClassVar[list] = []

    @classmethod
    def base_dir(cls):
        return os.path.join(current_app.config['VIZAR_DATA_DIR'], 'work_items')

    def delete(self):
        item_path = WorkItem.item_dir(self.id)
        shutil.rmtree(item_path, ignore_errors=True)

    @classmethod
    def find(cls, **kwargs):
        work_item_dir = cls.base_dir()
        os.makedirs(work_item_dir, exist_ok=True)

        query = dict(after=0, contentType=None, sourceType=None, status=None)
        query.update(kwargs)

        work_items = []
        for dname in os.listdir(work_item_dir):
            if not os.path.isdir(dname) or dname == "data":
                continue
            fname = os.path.join(dname, "work-item.json")
            with open(fname, 'r') as source:
                item = cls.Schema().loads(source.read())
                if item.matches(query):
                    work_items.append(item)

        return work_items

    @classmethod
    def find_by_id(cls, item_id):
        path = os.path.join(cls.item_dir(item_id), "work-item.json")
        try:
            with open(path, 'r') as source:
                item = cls.Schema().loads(source.read())
                return item
        except:
            return None

    @classmethod
    def get_next_id(cls):
        next_id = cls.next_id

        if next_id == 0:
            items = cls.find()
            if len(items) > 0:
                next_id = max(item.id for item in items) + 1
            else:
                next_id = 1

        cls.next_id = next_id + 1
        return next_id

    @classmethod
    def item_dir(cls, item_id):
        return os.path.join(cls.base_dir(), "{:08x}".format(item_id))

    def matches(self, query):
        return self.id > int(query.get('after', 0)) and \
                query.get('contentType') in (None, self.contentType) and \
                query.get('sourceType') in (None, self.sourceType) and \
                query.get('status') in (None, self.status)

    def save(self):
        work_item_dir = WorkItem.item_dir(self.id)
        os.makedirs(work_item_dir, exist_ok=True)
        path = os.path.join(work_item_dir, "work-item.json")

        # Also create a directory for uploads.
        os.makedirs(self.uploads_dir(), exist_ok=True)

        # Check if this is a new object.
        created = not os.path.exists(path)

        self.updated = time.time()

        with open(path, 'w') as output:
            json_out = self.Schema().dumps(self)
            output.write(json_out)

        # Notify any listeners if this is a new object.
        if created:
            remaining_listeners = []
            for future, query in self.on_create:
                if future.cancelled():
                    continue
                elif self.matches(query):
                    future.set_result(self)
                else:
                    remaining_listeners.append((future, query))

            self.on_create.clear()
            self.on_create.extend(remaining_listeners)

        return created

    def uploads_dir(self):
        return os.path.join(WorkItem.item_dir(self.id), "uploads")

    @classmethod
    async def wait_for_work_item(cls, **kwargs):
        query = dict(after=0, contentType=None, sourceType=None, status=None)
        query.update(kwargs)

        future = asyncio.get_event_loop().create_future()

        cls.on_create.append((future, query))

        return await future
