from server.handlers.context_handler import ContextHandler


def test_provider_validation():
    ctx = ContextHandler()
    ctx.set_ai_provider("claude")
    ctx.set_ai_provider("droid")
    ctx.set_ai_provider("gemini")

    try:
        ctx.set_ai_provider("unknown")
        raise AssertionError("ValueError expected for invalid provider")
    except ValueError:
        pass


def test_system_prompt_variants():
    ctx = ContextHandler()

    # 기본(진행자 없음)
    p0 = ctx.build_system_prompt()
    assert "performs the roles of multiple characters" in p0

    # 사용자 진행자
    ctx.set_narrator(enabled=False, user_is_narrator=True)
    p1 = ctx.build_system_prompt()
    assert "user serves as the Game Master" in p1

    # AI 진행자
    ctx.set_narrator(enabled=True, mode="active", description="", user_is_narrator=False)
    p2 = ctx.build_system_prompt()
    assert "TRPG Game Master" in p2 or "narrator role" in p2

    # 진행자 모드: passive 분기
    ctx.set_narrator(enabled=True, mode="passive", description="", user_is_narrator=False)
    p3 = ctx.build_system_prompt()
    assert "Narrator Mode: Passive" in p3


def test_adult_level_affects_prompt():
    ctx = ContextHandler()
    ctx.set_adult_level("enhanced")
    p_enh = ctx.build_system_prompt()
    assert "Content Level: Enhanced" in p_enh

    ctx.set_adult_level("extreme")
    p_ext = ctx.build_system_prompt()
    # 극단 수위 문구 일부 확인
    assert "Content Level: Extreme" in p_ext


def test_full_context_sections_and_separation():
    ctx = ContextHandler()
    ctx.set_world("중세 판타지 왕국")
    ctx.set_situation("마을 축제의 밤")
    ctx.set_user_character("용사: 검을 든 여행자")
    ctx.set_characters(
        [
            {"name": "민수", "description": "쾌활한 도적"},
            {"name": "지은", "description": "온화한 사제"},
        ]
    )
    ctx.set_narrative_separation(True)

    prompt = ctx.build_system_prompt("HIST")
    assert "Expression Separation Mode" in prompt
    assert "=== World Setting ===\n중세 판타지 왕국" in prompt
    assert "=== Current Situation ===\n마을 축제의 밤" in prompt
    assert "=== Conversation Partner (User) ===\n용사: 검을 든 여행자" in prompt
    assert "=== Characters ===" in prompt
    assert "[민수]" in prompt and "[지은]" in prompt
    assert "Dialogue Rules" in prompt or "Response Example" in prompt
