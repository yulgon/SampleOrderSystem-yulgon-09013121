from dataclasses import dataclass


@dataclass
class ProductionQueueEntry:
    order_id: int
    sample_id: int
    shortfall: int
    actual_qty: int
    total_time: float
    entry_id: int = None

    def __post_init__(self):
        if self.shortfall <= 0:
            raise ValueError("shortfall must be positive")
        if self.actual_qty <= 0:
            raise ValueError("actual_qty must be positive")
        if self.total_time <= 0:
            raise ValueError("total_time must be positive")

    def to_dict(self):
        data = {
            "order_id": self.order_id,
            "sample_id": self.sample_id,
            "shortfall": self.shortfall,
            "actual_qty": self.actual_qty,
            "total_time": self.total_time,
        }
        if self.entry_id is not None:
            data["id"] = self.entry_id
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            order_id=data["order_id"],
            sample_id=data["sample_id"],
            shortfall=data["shortfall"],
            actual_qty=data["actual_qty"],
            total_time=data["total_time"],
            entry_id=data.get("id"),
        )
