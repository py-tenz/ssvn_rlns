from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING
from pymongo.errors import PyMongoError

@dataclass
class Mongo:
    uri: str
    db_name: str

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        self.client = AsyncIOMotorClient(self.uri)
        self.db = self.client[self.db_name]
        await self.ensure_indexes()

    async def close(self) -> None:
        if self.client:
            self.client.close()

    @property
    def users(self):
        assert self.db is not None
        return self.db["users"]

    @property
    def lessons(self):
        assert self.db is not None
        return self.db["lessons"]

    async def ensure_indexes(self) -> None:
        """Create indexes used by the bot. Safe to call on every startup."""
        assert self.db is not None
        # users: _id = telegram user id (int)
        await self.users.create_index([("created_at", ASCENDING)])
        await self.users.create_index([("updated_at", ASCENDING)])
        await self.users.create_index([("next_unlock_at", ASCENDING)])
        # lessons: unique dayNum
        await self.lessons.create_index([("dayNum", ASCENDING)], unique=True)

    # ---------- Users ----------
    async def get_user(self, tg_id: int) -> Optional[dict[str, Any]]:
        try:
            return await self.users.find_one({"_id": tg_id})
        except PyMongoError:
            return None

    async def create_user(self, tg_id: int, name: str, birth_year: int) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        doc = {
            "_id": tg_id,
            "name": name,
            "birth_year": birth_year,
            "entry_test_completed": False,
            "completed_day": 0,  # last fully completed day (0 = none)
            # When the next day becomes available (UTC datetime). Missing/None => unlocked.
            "next_unlock_at": None,
            "last_completed_at": None,
            "created_at": now,
            "updated_at": now,
        }
        await self.users.insert_one(doc)
        return doc

    async def set_entry_test_completed(self, tg_id: int, completed: bool = True) -> None:
        now = datetime.now(timezone.utc)
        await self.users.update_one(
            {"_id": tg_id},
            {"$set": {"entry_test_completed": completed, "updated_at": now}},
            upsert=False,
        )

    async def set_completed_day(self, tg_id: int, completed_day: int) -> None:
        now = datetime.now(timezone.utc)
        await self.users.update_one(
            {"_id": tg_id},
            {"$set": {"completed_day": completed_day, "updated_at": now}},
            upsert=False,
        )

    async def mark_day_completed(
        self,
        *,
        tg_id: int,
        completed_day: int,
        next_unlock_at: datetime,
        last_completed_at: datetime,
    ) -> None:
        """Mark day as completed and set next unlock moment.

        All datetimes are expected to be timezone-aware UTC.
        """
        now = datetime.now(timezone.utc)
        await self.users.update_one(
            {"_id": tg_id},
            {
                "$set": {
                    "completed_day": completed_day,
                    "next_unlock_at": next_unlock_at,
                    "last_completed_at": last_completed_at,
                    "updated_at": now,
                }
            },
            upsert=False,
        )

    # ---------- Lessons ----------
    async def get_lesson(self, day_num: int) -> Optional[dict[str, Any]]:
        try:
            return await self.lessons.find_one({"dayNum": day_num})
        except PyMongoError:
            return None

    async def get_max_day(self) -> int:
        """Returns maximal dayNum present in DB (0 if empty)."""
        try:
            doc = await self.lessons.find().sort("dayNum", -1).limit(1).to_list(length=1)
            return int(doc[0]["dayNum"]) if doc else 0
        except Exception:
            return 0

    async def get_days(self, skip: int = 0, limit: int = 10, max_day_num: Optional[int] = None) -> list[int]:
        try:
            q: dict[str, Any] = {}
            if max_day_num is not None:
                q = {"dayNum": {"$lte": int(max_day_num)}}

            cursor = self.lessons.find(q, {"dayNum": 1, "_id": 0}).sort("dayNum", 1).skip(skip).limit(limit)
            docs = await cursor.to_list(length=limit)
            return [int(d["dayNum"]) for d in docs]
        except Exception:
            return []
