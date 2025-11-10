from server.handlers.context_handler import ContextHandler


def test_provider_validation():
    ctx = ContextHandler()
    ctx.set_ai_provider("claude")
    ctx.set_ai_provider("droid")
    ctx.set_ai_provider("gemini")

    try:
        ctx.set_ai_provider("unknown")
        assert False, "ValueError expected for invalid provider"
    except ValueError:
        pass


def test_system_prompt_variants():
    ctx = ContextHandler()

    # 기본(진행자 없음)
    p0 = ctx.build_system_prompt()
    assert "여러 캐릭터의 역할" in p0

    # 사용자 진행자
    ctx.set_narrator(enabled=False, user_is_narrator=True)
    p1 = ctx.build_system_prompt()
    assert "사용자는 진행자(GM) 역할" in p1

    # AI 진행자
    ctx.set_narrator(enabled=True, mode="active", description="", user_is_narrator=False)
    p2 = ctx.build_system_prompt()
    assert "TRPG의 GM(Game Master)처럼" in p2


def test_adult_level_affects_prompt():
    ctx = ContextHandler()
    ctx.set_adult_level("enhanced")
    p_enh = ctx.build_system_prompt()
    assert "콘텐츠 수위: 강화" in p_enh

    ctx.set_adult_level("extreme")
    p_ext = ctx.build_system_prompt()
    # 극단 수위 문구 일부 확인
    assert "최고 수위" in p_ext or "극단" in p_ext

