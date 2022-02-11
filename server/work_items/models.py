import asyncio
import glob
import os
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
    def get_all(cls, **kwargs):
        work_item_dir = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'work_items')
        os.makedirs(work_item_dir, exist_ok=True)

        query = dict(after=0, contentType=None, sourceType=None, status=None)
        query.update(kwargs)

        work_items = []
        for fname in glob.glob(os.path.join(work_item_dir, '*.json')):
            with open(fname, 'r') as source:
                item = cls.Schema().loads(source.read())
                if item.matches(query):
                    work_items.append(item)

        return work_items

    @classmethod
    def get_next_id(cls):
        next_id = cls.next_id

        if next_id == 0:
            items = cls.get_all()
            if len(items) > 0:
                next_id = max(item.id for item in items) + 1
            else:
                next_id = 1

        cls.next_id = next_id + 1
        return next_id

    def save(self):
        work_item_dir = os.path.join(current_app.config['VIZAR_DATA_DIR'], 'work_items')
        os.makedirs(work_item_dir, exist_ok=True)

        fname = "{:08x}.json".format(self.id)
        path = os.path.join(work_item_dir, fname)

        # Check if this is a new object.
        created = not os.path.exists(path)

        with open(path, 'w') as source:
            json_out = self.Schema().dumps(self)
            source.write(json_out)

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

    def matches(self, query):
        return self.id > int(query.get('after', 0)) and \
                query.get('contentType') in (None, self.contentType) and \
                query.get('sourceType') in (None, self.sourceType) and \
                query.get('status') in (None, self.status)

    @classmethod
    async def wait_for_work_item(cls, **kwargs):
        query = dict(after=0, contentType=None, sourceType=None, status=None)
        query.update(kwargs)

        future = asyncio.get_event_loop().create_future()

        cls.on_create.append((future, query))

        return await future
