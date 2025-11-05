from collections import deque


class HistoryHandler:
    """대화 히스토리 관리 (최근 N턴 유지)"""

    def __init__(self, max_turns=15):
        """
        Args:
            max_turns: 유지할 최대 턴 수 (기본 15턴)
        """
        self.max_turns = max_turns
        self.history = deque(maxlen=max_turns)  # 자동으로 오래된 것 제거

    def add_user_message(self, content):
        """사용자 메시지 추가"""
        self.history.append({
            "role": "user",
            "content": content
        })

    def add_assistant_message(self, content):
        """AI 응답 추가"""
        self.history.append({
            "role": "assistant",
            "content": content
        })

    def get_history(self):
        """전체 히스토리 반환"""
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

    def get_narrative_markdown(self):
        """서사 형식으로 마크다운 생성 (우측 패널 표시용)"""
        if not self.history:
            return "# 서사 기록\n\n아직 대화가 없습니다.\n"

        md = "# 서사 기록\n\n"

        for i, msg in enumerate(self.history, 1):
            if msg["role"] == "user":
                md += f"## {i}. 사용자\n\n{msg['content']}\n\n"
            else:
                md += f"## {i}. AI 응답\n\n{msg['content']}\n\n"
                md += "---\n\n"

        return md

    def __len__(self):
        """히스토리 길이"""
        return len(self.history)
