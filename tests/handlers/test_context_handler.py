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


def test_output_level_setter():
    """출력 레벨 설정 테스트"""
    ctx = ContextHandler()

    # 유효한 값
    ctx.set_output_level("less")
    assert ctx.current_context["output_level"] == "less"

    ctx.set_output_level("normal")
    assert ctx.current_context["output_level"] == "normal"

    ctx.set_output_level("more")
    assert ctx.current_context["output_level"] == "more"

    # 유효하지 않은 값은 normal로
    ctx.set_output_level("invalid")
    assert ctx.current_context["output_level"] == "normal"

    ctx.set_output_level(None)
    assert ctx.current_context["output_level"] == "normal"


def test_narrator_drive_setter():
    """진행자 주도권 설정 테스트"""
    ctx = ContextHandler()

    # 유효한 값
    ctx.set_narrator_drive("describe")
    assert ctx.current_context["narrator_drive"] == "describe"

    ctx.set_narrator_drive("guide")
    assert ctx.current_context["narrator_drive"] == "guide"

    ctx.set_narrator_drive("direct")
    assert ctx.current_context["narrator_drive"] == "direct"

    # 유효하지 않은 값은 guide로
    ctx.set_narrator_drive("invalid")
    assert ctx.current_context["narrator_drive"] == "guide"


def test_choice_policy_setter():
    """선택지 정책 설정 테스트"""
    ctx = ContextHandler()

    # 유효한 값
    ctx.set_choice_policy("off")
    assert ctx.current_context["choice_policy"] == "off"

    ctx.set_choice_policy("require")
    assert ctx.current_context["choice_policy"] == "require"

    # 유효하지 않은 값은 off로
    ctx.set_choice_policy("invalid")
    assert ctx.current_context["choice_policy"] == "off"


def test_choice_count_setter():
    """선택지 개수 설정 테스트"""
    ctx = ContextHandler()

    # 유효한 값
    ctx.set_choice_count(3)
    assert ctx.current_context["choice_count"] == 3

    # 범위 초과 값은 제한됨 (2-5)
    ctx.set_choice_count(1)
    assert ctx.current_context["choice_count"] == 2

    ctx.set_choice_count(10)
    assert ctx.current_context["choice_count"] == 5

    # 유효하지 않은 값은 3으로
    ctx.set_choice_count("invalid")
    assert ctx.current_context["choice_count"] == 3


def test_load_from_dict():
    """dict에서 컨텍스트 로드 테스트"""
    ctx = ContextHandler()

    context_dict = {
        "world": "테스트 세계",
        "situation": "테스트 상황",
        "user_character": "테스트 캐릭터",
        "characters": [{"name": "캐릭터1", "description": "설명1"}],
        "narrator_enabled": True,
        "narrator_mode": "active",
        "narrator_description": "테스트 진행자",
        "user_is_narrator": False,
        "adult_level": "enhanced",
        "narrative_separation": True,
        "ai_provider": "gemini",
        "output_level": "more",
        "narrator_drive": "direct",
        "choice_policy": "require",
        "choice_count": 4,
    }

    ctx.load_from_dict(context_dict)

    # 모든 설정이 올바르게 로드되었는지 확인
    assert ctx.current_context["world"] == "테스트 세계"
    assert ctx.current_context["situation"] == "테스트 상황"
    assert ctx.current_context["user_character"] == "테스트 캐릭터"
    assert len(ctx.current_context["characters"]) == 1
    assert ctx.current_context["narrator_enabled"] is True
    assert ctx.current_context["narrator_mode"] == "active"
    assert ctx.current_context["adult_level"] == "enhanced"
    assert ctx.current_context["narrative_separation"] is True
    assert ctx.current_context["ai_provider"] == "gemini"
    assert ctx.current_context["output_level"] == "more"
    assert ctx.current_context["narrator_drive"] == "direct"
    assert ctx.current_context["choice_policy"] == "require"
    assert ctx.current_context["choice_count"] == 4

    # 유효하지 않은 입력 처리
    ctx.load_from_dict("not a dict")  # 아무 일도 일어나지 않아야 함
    ctx.load_from_dict(None)  # 아무 일도 일어나지 않아야 함
