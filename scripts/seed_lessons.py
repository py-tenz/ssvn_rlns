"""Seed lessons into MongoDB from JSON.

Usage:
  python scripts/seed_lessons.py lessons.json mongodb://localhost:27017 pilot_training
JSON format (recommended):
  [
    {
      "dayNum": 1,
      "tasks": [
        {"text": "Задание 1...", "images": ["a.jpg", "b.jpg"]},
        {"text": "Задание 2...", "images": []}
      ]
    },
    ...
  ]

Legacy format is also supported and will be converted into a single task:
  {"dayNum": 1, "text": "...", "images": ["a.jpg"]}
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

        # Normalize to tasks
        tasks = item.get("tasks")
        if isinstance(tasks, list) and tasks:
            norm_tasks = []
            for t in tasks:
                if not isinstance(t, dict):
                    continue
                t_text = str(t.get("text", ""))
                t_images = t.get("images") or []
                if not isinstance(t_images, list):
                    t_images = []
                norm_tasks.append({"text": t_text, "images": t_images})
            if not norm_tasks:
                norm_tasks = [{"text": "", "images": []}]
        else:
            # legacy
            text = str(item.get("text", ""))
            images = item.get("images") or []
            if not isinstance(images, list):
                images = []
            norm_tasks = [{"text": text, "images": images}]

        ops.append(
            UpdateOne(
                {"dayNum": day},
                {"$set": {"dayNum": day, "tasks": norm_tasks}},
                upsert=True,
            )
        )

    if ops:
        res = col.bulk_write(ops)
        print("Seed done:", res.bulk_api_result)
    else:
        print("Nothing to seed.")

if __name__ == "__main__":
    main()
