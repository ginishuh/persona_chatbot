"""토큰 사용량 추적 핸들러

모델별(Claude/Gemini/Droid) 토큰 사용량을 누적하고 관리합니다.
"""

import logging

logger = logging.getLogger(__name__)


class TokenUsageHandler:
    """토큰 사용량 추적 및 누적 관리"""

    def __init__(self):
        # 세션별 토큰 사용량: { session_key: { room_id: { provider: usage_dict } } }
        self.session_usage: dict[str, dict[str, dict[str, dict]]] = {}

    def add_usage(
        self,
        session_key: str,
        room_id: str,
        provider: str,
        token_info: dict | None,
    ):
        """토큰 사용량 추가

        Args:
            session_key: 세션 키
            room_id: 채팅방 ID
            provider: AI 제공자 (claude/gemini/droid)
            token_info: 토큰 정보 딕셔너리 (None일 경우 미지원으로 처리)
        """
        if token_info is None:
            # 토큰 정보를 제공하지 않는 제공자
            logger.debug(f"Provider {provider} does not provide token usage info")
            return

        # 세션 초기화
        if session_key not in self.session_usage:
            self.session_usage[session_key] = {}

        # 채팅방 초기화
        if room_id not in self.session_usage[session_key]:
            self.session_usage[session_key][room_id] = {}

        # 제공자 초기화
        if provider not in self.session_usage[session_key][room_id]:
            self.session_usage[session_key][room_id][provider] = {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cache_read_tokens": 0,
                "total_cache_creation_tokens": 0,
                "total_tokens": 0,
                "message_count": 0,
                "last_input_tokens": 0,
                "last_output_tokens": 0,
                "last_cache_read_tokens": 0,
                "last_cache_creation_tokens": 0,
                "last_total_tokens": 0,
            }

        usage = self.session_usage[session_key][room_id][provider]

        # 현재 토큰 정보 추출
        input_tokens = token_info.get("input_tokens", 0)
        output_tokens = token_info.get("output_tokens", 0)
        cache_read = token_info.get("cache_read_tokens", 0)
        cache_creation = token_info.get("cache_creation_tokens", 0)
        total = token_info.get(
            "total_tokens", input_tokens + output_tokens + cache_read + cache_creation
        )

        # 누적
        usage["total_input_tokens"] += input_tokens
        usage["total_output_tokens"] += output_tokens
        usage["total_cache_read_tokens"] += cache_read
        usage["total_cache_creation_tokens"] += cache_creation
        usage["total_tokens"] += total
        usage["message_count"] += 1

        # 최근 사용량
        usage["last_input_tokens"] = input_tokens
        usage["last_output_tokens"] = output_tokens
        usage["last_cache_read_tokens"] = cache_read
        usage["last_cache_creation_tokens"] = cache_creation
        usage["last_total_tokens"] = total

        logger.info(
            f"Token usage updated - session: {session_key[:8]}..., "
            f"room: {room_id}, provider: {provider}, "
            f"last: {total}, total: {usage['total_tokens']}"
        )

    def get_usage(
        self,
        session_key: str,
        room_id: str,
        provider: str | None = None,
    ) -> dict:
        """토큰 사용량 조회

        Args:
            session_key: 세션 키
            room_id: 채팅방 ID
            provider: AI 제공자 (None이면 전체)

        Returns:
            토큰 사용량 딕셔너리
        """
        if session_key not in self.session_usage:
            return {}

        if room_id not in self.session_usage[session_key]:
            return {}

        room_usage = self.session_usage[session_key][room_id]

        if provider:
            # 특정 제공자만 반환
            return {provider: room_usage.get(provider, {})}
        else:
            # 모든 제공자 반환
            return room_usage

    def clear_usage(
        self,
        session_key: str,
        room_id: str | None = None,
    ):
        """토큰 사용량 초기화

        Args:
            session_key: 세션 키
            room_id: 채팅방 ID (None이면 전체 세션)
        """
        if session_key not in self.session_usage:
            return

        if room_id:
            # 특정 채팅방만 초기화
            if room_id in self.session_usage[session_key]:
                del self.session_usage[session_key][room_id]
                logger.info(f"Token usage cleared - session: {session_key[:8]}..., room: {room_id}")
        else:
            # 세션 전체 초기화
            del self.session_usage[session_key]
            logger.info(f"Token usage cleared - session: {session_key[:8]}...")

    def get_formatted_summary(
        self,
        session_key: str,
        room_id: str,
    ) -> dict:
        """UI 표시용 포맷된 요약 정보

        Returns:
            {
                "providers": {
                    "claude": {
                        "supported": true,
                        "total_tokens": 1000,
                        "last_tokens": 50,
                        ...
                    },
                    "gemini": {
                        "supported": false,
                        "message": "토큰 정보 제공 안 됨"
                    }
                }
            }
        """
        usage = self.get_usage(session_key, room_id)

        result = {
            "providers": {
                "claude": {"supported": False, "message": "사용 기록 없음"},
                "gemini": {"supported": False, "message": "토큰 정보 제공 안 됨"},
                "droid": {"supported": False, "message": "토큰 정보 제공 안 됨"},
            }
        }

        for provider, provider_usage in usage.items():
            if provider_usage and provider_usage.get("message_count", 0) > 0:
                result["providers"][provider] = {
                    "supported": True,
                    "total_input_tokens": provider_usage["total_input_tokens"],
                    "total_output_tokens": provider_usage["total_output_tokens"],
                    "total_cache_read_tokens": provider_usage["total_cache_read_tokens"],
                    "total_cache_creation_tokens": provider_usage["total_cache_creation_tokens"],
                    "total_tokens": provider_usage["total_tokens"],
                    "message_count": provider_usage["message_count"],
                    "last_input_tokens": provider_usage["last_input_tokens"],
                    "last_output_tokens": provider_usage["last_output_tokens"],
                    "last_cache_read_tokens": provider_usage["last_cache_read_tokens"],
                    "last_cache_creation_tokens": provider_usage["last_cache_creation_tokens"],
                    "last_total_tokens": provider_usage["last_total_tokens"],
                }

        return result
