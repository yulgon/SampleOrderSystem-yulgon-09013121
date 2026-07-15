from model.sample import Sample
from persistence.repository import JsonRepository


class SampleRepository:
    def __init__(self, base_dir="data"):
        self._repo = JsonRepository("samples", base_dir=base_dir)

    def create(self, sample):
        record = self._repo.create(sample.to_dict())
        return Sample.from_dict(record)

    def get(self, sample_id):
        record = self._repo.get(sample_id)
        return Sample.from_dict(record) if record else None

    def list_all(self):
        return [Sample.from_dict(record) for record in self._repo.list_all()]

    def update(self, sample_id, changes):
        record = self._repo.update(sample_id, changes)
        return Sample.from_dict(record) if record else None

    def delete(self, sample_id):
        return self._repo.delete(sample_id)
