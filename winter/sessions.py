from dataclasses import is_dataclass, asdict
from typing import Any
from winter.drivers.mongo import MongoDbDriver, MongoSession, get_tablename
from winter.backend import Backend
from winter.utils.keys import __winter_track_target__


class MongoSessionTracker:
    """
    Tracks changes on objects returned by a repository
    and updates then after command
    """

    def __init__(self, owner: type) -> None:
        self.owner = owner
        self._modified = list()

    def add(self, instance: Any):
        if (target := getattr(instance, __winter_track_target__, None)) is not None:
            if target not in self._modified:
                assert is_dataclass(target)
                self._modified.append(target)

    async def flush(self, session: MongoSession):
        assert Backend.driver is not None
        assert isinstance(Backend.driver, MongoDbDriver)

        db = Backend.get_connection()
        collection = db[get_tablename(self.owner)]

        for modified_instance in self._modified:
            if (_id := getattr(modified_instance, "id", None)) is not None:
                values = asdict(modified_instance)
                values.pop("id", None)
                await collection.update_one({"id": _id}, {"$set": values}, session=session)

        self._modified = list()

    def clean(self):
        self._modified = list()