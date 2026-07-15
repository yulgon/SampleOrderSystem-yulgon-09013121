from dataclasses import dataclass


class OrderStatus:
    RESERVED = "RESERVED"
    REJECTED = "REJECTED"
    PRODUCING = "PRODUCING"
    CONFIRMED = "CONFIRMED"
    RELEASE = "RELEASE"

    ALL = (RESERVED, REJECTED, PRODUCING, CONFIRMED, RELEASE)


@dataclass
class Order:
    sample_id: int
    customer: str
    qty: int
    status: str
    order_id: int = None

    def __post_init__(self):
        if self.qty <= 0:
            raise ValueError("qty must be positive")
        if self.status not in OrderStatus.ALL:
            raise ValueError(f"invalid status: {self.status}")

    def to_dict(self):
        data = {
            "sample_id": self.sample_id,
            "customer": self.customer,
            "qty": self.qty,
            "status": self.status,
        }
        if self.order_id is not None:
            data["id"] = self.order_id
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            sample_id=data["sample_id"],
            customer=data["customer"],
            qty=data["qty"],
            status=data["status"],
            order_id=data.get("id"),
        )
