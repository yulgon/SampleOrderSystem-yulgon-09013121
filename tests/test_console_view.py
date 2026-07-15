from view.console_view import ConsoleView


def test_show_menu_prints_title_and_numbered_options(capsys):
    view = ConsoleView()
    view.show_menu("시료 관리", [(1, "시료 등록"), (2, "시료 조회"), (3, "시료 검색"), (4, "돌아가기")])
    captured = capsys.readouterr()
    assert "시료 관리" in captured.out
    assert "1. 시료 등록" in captured.out
    assert "4. 돌아가기" in captured.out


def test_show_message_prints_the_message(capsys):
    view = ConsoleView()
    view.show_message("hello")
    captured = capsys.readouterr()
    assert "hello" in captured.out


def test_show_status_bar_prints_all_four_values(capsys):
    view = ConsoleView()
    view.show_status_bar(registered_samples=2, total_stock=15, total_orders=3, waiting_lines=1)
    captured = capsys.readouterr()
    assert "등록시료: 2" in captured.out
    assert "총 재고: 15" in captured.out
    assert "전체주문: 3" in captured.out
    assert "대기중인 생산라인: 1" in captured.out
