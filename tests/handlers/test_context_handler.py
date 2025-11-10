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

    # 진행자 모드: passive 분기
    ctx.set_narrator(enabled=True, mode="passive", description="", user_is_narrator=False)
    p3 = ctx.build_system_prompt()
    assert "진행자 모드: 소극적" in p3


def test_adult_level_affects_prompt():
    ctx = ContextHandler()
    ctx.set_adult_level("enhanced")
    p_enh = ctx.build_system_prompt()
    assert "콘텐츠 수위: 강화" in p_enh

    ctx.set_adult_level("extreme")
    p_ext = ctx.build_system_prompt()
    # 극단 수위 문구 일부 확인
    assert "최고 수위" in p_ext or "극단" in p_ext


def test_full_context_sections_and_separation():
    ctx = ContextHandler()
    ctx.set_world("중세 판타지 왕국")
    ctx.set_situation("마을 축제의 밤")
    ctx.set_user_character("용사: 검을 든 여행자")
    ctx.set_characters([
        {"name": "민수", "description": "쾌활한 도적"},
        {"name": "지은", "description": "온화한 사제"},
    ])
    ctx.set_narrative_separation(True)

    prompt = ctx.build_system_prompt("HIST")
    assert "표현 분리 모드" in prompt
    assert "=== 세계관 ===\n중세 판타지 왕국" in prompt
    assert "=== 현재 상황 ===\n마을 축제의 밤" in prompt
    assert "=== 대화 상대 (사용자) ===\n용사: 검을 든 여행자" in prompt
    assert "=== 등장 캐릭터들 ===" in prompt
    assert "[민수]" in prompt and "[지은]" in prompt
    assert prompt.endswith("대화하세요\n\n응답 예시:\n[민수]: 오 그거 좋은데? 나도 갈래!\n[지은]: 민수야, 너 숙제는 다 했어?\n[민수]: 아... 그게... 나중에 할게ㅋㅋ\n\n" ) or "대화 규칙" in prompt
