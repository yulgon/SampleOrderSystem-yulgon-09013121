from model.sample import Sample
from persistence.sample_repository import SampleRepository


class SampleController:
    MENU_TITLE = "시료 관리"
    MENU_OPTIONS = [(1, "시료 등록"), (2, "시료 조회"), (3, "시료 검색"), (4, "돌아가기")]

    def __init__(self, view, base_dir="data"):
        self.view = view
        self.repository = SampleRepository(base_dir=base_dir)

    def run(self):
        while True:
            self.view.show_menu(self.MENU_TITLE, self.MENU_OPTIONS)
            choice = self.view.get_input("메뉴 번호를 입력하세요: ")

            if choice == "1":
                self._register()
            elif choice == "2":
                self._list()
            elif choice == "3":
                self._search()
            elif choice == "4":
                return
            else:
                self.view.show_message("잘못된 입력입니다.")

    def _prompt_float(self, prompt, error_message, is_valid):
        while True:
            raw = self.view.get_input(prompt)
            try:
                value = float(raw)
            except ValueError:
                self.view.show_message("숫자를 입력해주세요.")
                continue
            if not is_valid(value):
                self.view.show_message(error_message)
                continue
            return value

    def _prompt_int(self, prompt, error_message, is_valid):
        while True:
            raw = self.view.get_input(prompt)
            try:
                value = int(raw)
            except ValueError:
                self.view.show_message("숫자를 입력해주세요.")
                continue
            if not is_valid(value):
                self.view.show_message(error_message)
                continue
            return value

    def _register(self):
        name = self.view.get_input("시료명: ")
        avg_production_time = self._prompt_float(
            "평균 생산시간: ",
            "평균 생산시간은 0보다 커야 합니다.",
            lambda v: v > 0,
        )
        yield_rate = self._prompt_float(
            "수율: ",
            "수율은 0~1 사이여야 합니다.",
            lambda v: 0 <= v <= 1,
        )
        stock = self._prompt_int(
            "현재 재고: ",
            "재고는 0 이상이어야 합니다.",
            lambda v: v >= 0,
        )
        sample = self.repository.create(
            Sample(
                name=name,
                avg_production_time=avg_production_time,
                yield_rate=yield_rate,
                stock=stock,
            )
        )
        self.view.show_message(
            f"시료 등록 완료: ID={sample.sample_id}, 이름={sample.name}, "
            f"평균생산시간={sample.avg_production_time}, 수율={sample.yield_rate}, "
            f"재고={sample.stock}"
        )

    def _list(self):
        samples = self.repository.list_all()
        if not samples:
            self.view.show_message("등록된 시료가 없습니다.")
            return
        for sample in samples:
            self.view.show_message(
                f"ID={sample.sample_id}, 이름={sample.name}, "
                f"평균생산시간={sample.avg_production_time}, 수율={sample.yield_rate}, "
                f"재고={sample.stock}"
            )

    def _search(self):
        keyword = self.view.get_input("검색어(이름): ")
        matches = [s for s in self.repository.list_all() if keyword in s.name]
        if not matches:
            self.view.show_message("일치하는 시료가 없습니다.")
            return
        for sample in matches:
            self.view.show_message(
                f"ID={sample.sample_id}, 이름={sample.name}, 재고={sample.stock}"
            )
