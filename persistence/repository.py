import json
import os


class JsonRepository:
    def __init__(self, collection_name, base_dir="data"):
        self.base_dir = base_dir
        self.path = os.path.join(base_dir, f"{collection_name}.json")

    def _load(self):
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, records):
        os.makedirs(self.base_dir, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    def list_all(self):
        return self._load()

    def get(self, record_id):
        for record in self._load():
            if record["id"] == record_id:
                return record
        return None

    def create(self, data):
        records = self._load()
        next_id = max((r["id"] for r in records), default=0) + 1
        record = {"id": next_id, **data}
        records.append(record)
        self._save(records)
        return record

    def update(self, record_id, data):
        records = self._load()
        for i, r in enumerate(records):
            if r["id"] == record_id:
                updated = {**r, **data, "id": record_id}
                records[i] = updated
                self._save(records)
                return updated
        return None

    def delete(self, record_id):
        records = self._load()
        for i, r in enumerate(records):
            if r["id"] == record_id:
                del records[i]
                self._save(records)
                return True
        return False
