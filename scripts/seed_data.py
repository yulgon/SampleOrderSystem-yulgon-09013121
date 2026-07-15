import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.sample import Sample
from model.order import Order, OrderStatus
from persistence.sample_repository import SampleRepository
from persistence.order_repository import OrderRepository


SAMPLES = [
    {"name": "Sample A", "avg_production_time": 2.0, "yield_rate": 0.9, "stock": 20},
    {"name": "Sample B", "avg_production_time": 1.5, "yield_rate": 0.8, "stock": 2},
    {"name": "Sample C", "avg_production_time": 3.0, "yield_rate": 0.95, "stock": 0},
    {"name": "Sample D", "avg_production_time": 2.5, "yield_rate": 0.85, "stock": 10},
]

# (index into SAMPLES, order qty)
ORDERS = [
    (0, 5),   # Sample A: sufficient (20 >= 5)
    (1, 10),  # Sample B: insufficient (2 < 10), shortfall 8
    (2, 3),   # Sample C: insufficient (0 < 3), shortfall 3
    (3, 5),   # Sample D: sufficient (10 >= 5)
    (3, 3),   # Sample D: sufficient (5 >= 3, after the order above is approved)
]


def main():
    if os.path.isdir("data"):
        print("data/ 디렉토리가 이미 존재합니다. 기존 데이터를 보호하기 위해 시딩을 중단합니다.")
        print("새로 시딩하려면 기존 data/ 디렉토리를 직접 삭제한 뒤 다시 실행하세요.")
        return

    sample_repo = SampleRepository()
    order_repo = OrderRepository()

    created_samples = []
    for spec in SAMPLES:
        sample = sample_repo.create(Sample(**spec))
        created_samples.append(sample)
        print(f"시료 생성: ID={sample.sample_id}, 이름={sample.name}, 재고={sample.stock}")

    created_orders = []
    for sample_index, qty in ORDERS:
        sample = created_samples[sample_index]
        order = order_repo.create(
            Order(sample_id=sample.sample_id, customer="Acme", qty=qty, status=OrderStatus.RESERVED)
        )
        created_orders.append(order)
        print(
            f"주문 생성: ID={order.order_id}, 시료ID={order.sample_id}, "
            f"수량={order.qty}, 상태={order.status}"
        )

    reread_samples = sample_repo.list_all()
    reread_orders = order_repo.list_all()

    assert len(reread_samples) == len(SAMPLES), (
        f"시료 개수 불일치: 기대 {len(SAMPLES)}, 실제 {len(reread_samples)}"
    )
    assert len(reread_orders) == len(ORDERS), (
        f"주문 개수 불일치: 기대 {len(ORDERS)}, 실제 {len(reread_orders)}"
    )
    for expected, actual in zip(created_samples, reread_samples):
        assert expected == actual, f"시료 데이터 불일치: {expected} != {actual}"
    for expected, actual in zip(created_orders, reread_orders):
        assert expected == actual, f"주문 데이터 불일치: {expected} != {actual}"

    print(f"\n시딩 완료: 시료 {len(reread_samples)}개, 주문 {len(reread_orders)}건 (재확인 통과)")


if __name__ == "__main__":
    main()
