"""HistoryHandler 단위 테스트

한국어 테스트 설명:
- 최근 N턴 윈도우 동작
- None(무제한) 모드 전환
- 마크다운 생성 포맷
- 초기화/예외 처리
"""

import re

from server.handlers.history_handler import HistoryHandler


def _roles(history):
    return [m["role"] for m in history]


def test_initial_state_and_empty_narrative():
    h = HistoryHandler()  # 기본 max_turns=15
    assert len(h) == 0
    assert h.get_history() == []
    assert h.get_history_text() == ""

    md = h.get_narrative_markdown()
    assert md.startswith("# 서사 기록\n\n")
    assert "아직 대화가 없습니다." in md


def test_window_enforced_and_full_history():
    h = HistoryHandler(max_turns=3)
    h.add_user_message("a")
    h.add_assistant_message("b")
    h.add_user_message("c")
    h.add_assistant_message("d")

    # 전체 기록은 4, 윈도우는 최근 3
    assert len(h.full_history) == 4
    assert len(h) == 3
    assert _roles(h.get_history()) == ["assistant", "user", "assistant"]


def test_set_max_turns_shrink_and_unlimited():
    h = HistoryHandler(max_turns=3)
    for i in range(5):
        if i % 2 == 0:
            h.add_user_message(f"u{i}")
        else:
            h.add_assistant_message(f"a{i}")

    assert len(h.full_history) == 5
    assert len(h) == 3

    # 더 작게 줄이면 윈도우도 줄어듦
    h.set_max_turns(2)
    assert len(h) == 2

    # 무제한 모드로 전환 → 윈도우=전체
    h.set_max_turns(None)
    assert len(h) == len(h.full_history)

    # 이후 추가해도 계속 누적됨
    h.add_assistant_message("more")
    assert len(h) == len(h.full_history)


def test_get_history_text_formatting():
    h = HistoryHandler(max_turns=3)
    h.add_user_message("안녕")
    h.add_assistant_message("반가워")

    text = h.get_history_text()
    assert text.startswith("=== 이전 대화 내역 ===\n")
    assert "사용자: 안녕" in text
    assert "AI: 반가워" in text
    assert "위 대화 내용을 참고" in text


def test_clear_and_len():
    h = HistoryHandler(max_turns=2)
    h.add_user_message("x")
    h.add_assistant_message("y")
    assert len(h) == 2

    h.clear()
    assert len(h) == 0
    assert h.get_history() == []
    assert "아직 대화가 없습니다." in h.get_narrative_markdown()


def test_invalid_max_turns_raises():
    h = HistoryHandler(max_turns=5)
    try:
        h.set_max_turns(0)
        raise AssertionError("ValueError expected")
    except ValueError as e:
        assert "positive" in str(e)


def test_narrative_markdown_format():
    h = HistoryHandler(max_turns=5)
    h.add_user_message("첫 메시지")
    h.add_assistant_message("첫 응답")

    md = h.get_narrative_markdown()
    # 섹션 헤더와 구분선 존재 확인
    assert re.search(r"##\s+1\.\s*사용자", md)
    assert re.search(r"##\s+2\.\s*AI 응답", md)
    assert "첫 메시지" in md and "첫 응답" in md
    assert "---\n\n" in md
