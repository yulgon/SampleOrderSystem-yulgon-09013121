from dataclasses import dataclass


@dataclass
class Sample:
    name: str
    avg_production_time: float
    yield_rate: float
    stock: int
    sample_id: int = None

    def __post_init__(self):
        if self.avg_production_time <= 0:
            raise ValueError("avg_production_time must be positive")
        if not (0 < self.yield_rate <= 1):
            raise ValueError("yield_rate must be greater than 0 and at most 1")
        if self.stock < 0:
            raise ValueError("stock must not be negative")

    def to_dict(self):
        data = {
            "name": self.name,
            "avg_production_time": self.avg_production_time,
            "yield_rate": self.yield_rate,
            "stock": self.stock,
        }
        if self.sample_id is not None:
            data["id"] = self.sample_id
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            avg_production_time=data["avg_production_time"],
            yield_rate=data["yield_rate"],
            stock=data["stock"],
            sample_id=data.get("id"),
        )
