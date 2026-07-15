from model.production_queue_entry import ProductionQueueEntry
from persistence.repository import JsonRepository


class ProductionQueueRepository:
    def __init__(self, base_dir="data"):
        self._repo = JsonRepository("production_queue", base_dir=base_dir)

    def create(self, entry):
        data = {k: v for k, v in entry.to_dict().items() if k != "id"}
        record = self._repo.create(data)
        return ProductionQueueEntry.from_dict(record)

    def list_all(self):
        return [ProductionQueueEntry.from_dict(record) for record in self._repo.list_all()]
