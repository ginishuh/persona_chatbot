from collections import deque


class HistoryHandler:
    """대화 히스토리 관리 (최근 N턴 + 전체 서사 유지)"""

    def __init__(self, max_turns=15):
        """
        Args:
            max_turns: 유지할 최대 턴 수 (기본 15턴, None이면 무제한)
        """
        self.max_turns = max_turns
        self.full_history: list[dict] = []  # 서사/다운로드용 전체 기록
        self.history = self._build_window_deque([])

    def _build_window_deque(self, snapshot):
        """현재 설정에 맞는 window deque 생성"""
        if self.max_turns is None:
            return deque(snapshot)
        return deque(snapshot[-self.max_turns :], maxlen=self.max_turns)

    def set_max_turns(self, max_turns):
        """맥락 길이 설정 (None이면 무제한)"""
        if max_turns is not None and max_turns <= 0:
            raise ValueError("max_turns must be positive or None")

        if max_turns == self.max_turns:
            return

        self.max_turns = max_turns
        self.history = self._build_window_deque(self.full_history)

    def _append_message(self, message):
        """공통 메시지 추가 로직"""
        self.full_history.append(message)
        self.history.append(message)

    def add_user_message(self, content):
        """사용자 메시지 추가"""
        self._append_message({"role": "user", "content": content})

    def add_assistant_message(self, content):
        """AI 응답 추가"""
        self._append_message({"role": "assistant", "content": content})

    def get_history(self):
        """현재 윈도우 히스토리 반환"""
        return list(self.history)

    def get_history_text(self):
        """히스토리를 텍스트로 변환 (System Prompt에 포함용)"""
        if not self.history:
            return ""

        text = "=== 이전 대화 내역 ===\n"
        for msg in self.history:
            role = "사용자" if msg["role"] == "user" else "AI"
            text += f"{role}: {msg['content']}\n"
        text += "\n위 대화 내용을 참고하여 자연스럽게 대화를 이어가세요.\n\n"
        return text

    def clear(self):
        """히스토리 초기화"""
        self.history.clear()
        self.full_history.clear()

    def get_narrative_markdown(self):
        """서사 형식으로 마크다운 생성 (우측 패널 표시용)"""
        if not self.full_history:
            return "# 서사 기록\n\n아직 대화가 없습니다.\n"

        md = "# 서사 기록\n\n"

        for i, msg in enumerate(self.full_history, 1):
            if msg["role"] == "user":
                md += f"## {i}. 사용자\n\n{msg['content']}\n\n"
            else:
                md += f"## {i}. AI 응답\n\n{msg['content']}\n\n"
                md += "---\n\n"

        return md

    def __len__(self):
        """현재 window 히스토리 길이"""
        return len(self.history)
