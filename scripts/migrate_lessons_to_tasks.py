"""Migrate legacy lessons (text/images) to tasks[] format.

Usage:
  python scripts/migrate_lessons_to_tasks.py MONGO_URI DB_NAME

What it does:
  - For every document in `lessons` without `tasks`, creates `tasks` as a single-item list
    containing the legacy `text` and `images`.
  - Safe to run multiple times.
"""

import sys

from pymongo import MongoClient


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python scripts/migrate_lessons_to_tasks.py MONGO_URI DB_NAME")
        raise SystemExit(1)

    mongo_uri = sys.argv[1]
    db_name = sys.argv[2]

    client = MongoClient(mongo_uri)
    db = client[db_name]
    col = db["lessons"]

    cursor = col.find({"tasks": {"$exists": False}})
    updated = 0
    for doc in cursor:
        day = int(doc.get("dayNum", 0) or 0)
        text = str(doc.get("text", ""))
        images = doc.get("images") or []
        if not isinstance(images, list):
            images = []
        col.update_one({"_id": doc["_id"]}, {"$set": {"tasks": [{"text": text, "images": images}]}})
        updated += 1

    print(f"Migration complete. Updated docs: {updated}")


if __name__ == "__main__":
    main()
