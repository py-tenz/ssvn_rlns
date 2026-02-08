"""Seed lessons into MongoDB from JSON.

Usage:
  python scripts/seed_lessons.py lessons.json mongodb://localhost:27017 pilot_training
JSON format:
  [
    {"dayNum": 1, "text": "...", "images": ["a.jpg", "b.jpg"]},
    ...
  ]
"""
import json
import sys
from pathlib import Path

from pymongo import MongoClient, UpdateOne

def main():
    if len(sys.argv) != 4:
        print("Usage: python scripts/seed_lessons.py lessons.json MONGO_URI DB_NAME")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    mongo_uri = sys.argv[2]
    db_name = sys.argv[3]

    lessons = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(lessons, list):
        raise SystemExit("JSON must be a list")

    client = MongoClient(mongo_uri)
    db = client[db_name]
    col = db["lessons"]

    ops = []
    for item in lessons:
        day = int(item["dayNum"])
        text = str(item.get("text", ""))
        images = item.get("images") or []
        if not isinstance(images, list):
            images = []
        ops.append(UpdateOne({"dayNum": day}, {"$set": {"dayNum": day, "text": text, "images": images}}, upsert=True))

    if ops:
        res = col.bulk_write(ops)
        print("Seed done:", res.bulk_api_result)
    else:
        print("Nothing to seed.")

if __name__ == "__main__":
    main()
