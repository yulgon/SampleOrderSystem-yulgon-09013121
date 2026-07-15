from model.sample import Sample
from persistence.repository import JsonRepository


class SampleRepository:
    def __init__(self, base_dir="data"):
        self._repo = JsonRepository("samples", base_dir=base_dir)

    def create(self, sample):
        data = {k: v for k, v in sample.to_dict().items() if k != "id"}
        record = self._repo.create(data)
        return Sample.from_dict(record)

    def get(self, sample_id):
        record = self._repo.get(sample_id)
        return Sample.from_dict(record) if record else None

    def list_all(self):
        return [Sample.from_dict(record) for record in self._repo.list_all()]

    def update(self, sample_id, changes):
        existing = self._repo.get(sample_id)
        if existing is None:
            return None
        Sample.from_dict({**existing, **changes})
        record = self._repo.update(sample_id, changes)
        return Sample.from_dict(record)

    def delete(self, sample_id):
        return self._repo.delete(sample_id)
