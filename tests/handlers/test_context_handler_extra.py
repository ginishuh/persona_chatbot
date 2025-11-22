from server.handlers.context_handler import ContextHandler


def test_output_drive_choice_and_sections():
    ctx = ContextHandler()

    # 진행자 ON, 설명 비움 -> 기본 문구 분기(231)
    ctx.set_narrator(enabled=True, mode="moderate", description="", user_is_narrator=False)

    # 진행자 주도: 안내형 + 선택지 강제(273~282)
    ctx.set_narrator_drive("guide")
    ctx.set_choice_policy("require")
    ctx.set_choice_count(9)  # 상한 5로 클램프

    # 출력량: more (318~322)
    ctx.set_output_level("more")

    # 등장 캐릭터/히스토리 섹션
    ctx.set_characters(
        [
            {"name": "민수", "description": "쾌활한 도적"},
            {"name": "지은", "description": "온화한 사제"},
        ]
    )

    prompt = ctx.build_system_prompt("HIST")

    # 진행자 보통 모드 분기(241~244)
    assert "Narrator Mode: Moderate" in prompt
    # 선택지 강제 섹션 및 상한 적용 확인
    assert "Choices (Required)" in prompt or "Minimum 5 choices" in prompt
    # 출력 예산: more 분기
    assert "8-12 lines" in prompt or "Output Budget" in prompt
    # 캐릭터/히스토리 섹션 포함
    assert "=== Characters ===" in prompt and "HIST" in prompt


def test_user_is_narrator_and_output_less():
    ctx = ContextHandler()
    # 사용자 진행자 모드 + 출력 적게(311~316)
    ctx.set_narrator(enabled=False, user_is_narrator=True)
    ctx.set_output_level("less")
    p = ctx.build_system_prompt()
    assert "user serves as the Game Master" in p
    assert "2-3 lines" in p or "Output Budget" in p


def test_direct_and_describe_modes_and_desc_present():
    ctx = ContextHandler()
    # 진행자 설명 제공(229), 모드 direct(259~265)
    ctx.set_narrator(
        enabled=True, mode="active", description="테스트 진행자", user_is_narrator=False
    )
    ctx.set_narrator_drive("direct")
    p1 = ctx.build_system_prompt()
    assert "테스트 진행자" in p1
    assert "Narrator Leadership Rules (Leadership Type)" in p1
    assert "Do not present choices" in p1

    # 설명형 describe 분기(267~271)
    ctx.set_narrator_drive("describe")
    p2 = ctx.build_system_prompt()
    assert "Narrator Leadership Rules (Description Type)" in p2


def test_input_sanitization_and_choice_count_bounds():
    ctx = ContextHandler()

    # 잘못된 값은 기본값으로 폴백
    ctx.set_output_level("invalid")
    ctx.set_narrator_drive("invalid")
    ctx.set_choice_policy("invalid")
    ctx.set_choice_count("not-a-number")

    c = ctx.get_context()
    assert c["output_level"] == "normal"
    assert c["narrator_drive"] == "guide"
    assert c["choice_policy"] == "off"
    assert c["choice_count"] == 3

    # 경계값 클램프(2~5)
    ctx.set_choice_count(1)
    assert ctx.get_context()["choice_count"] == 2
    ctx.set_choice_count(10)
    assert ctx.get_context()["choice_count"] == 5


def test_load_from_dict_applies_conversation_mode():
    ctx = ContextHandler()
    ctx.load_from_dict({"conversation_mode": "one_to_one_chat", "world": "w"})
    c = ctx.get_context()
    assert c["conversation_mode"] == "one_to_one_chat"
    assert c["world"] == "w"


def test_load_from_dict_resets_conversation_mode_when_missing():
    ctx = ContextHandler()
    # 먼저 다른 모드로 설정
    ctx.set_conversation_mode("one_to_one_drama")
    # 새 dict에 모드 키가 없어도 기본값으로 리셋되어야 한다
    ctx.load_from_dict({"world": "new"})
    c = ctx.get_context()
    assert c["conversation_mode"] == "trpg_multi"
    assert c["world"] == "new"
