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
    assert "진행자 모드: 보통" in prompt
    # 선택지 강제 섹션 및 상한 적용 확인
    assert "선택지(필수)" in prompt and "최소 5개" in prompt
    # 출력 예산: more 분기
    assert "이번 턴: 총 8~12줄" in prompt
    # 캐릭터/히스토리 섹션 포함
    assert "=== 등장 캐릭터들 ===" in prompt and "HIST" in prompt


def test_user_is_narrator_and_output_less():
    ctx = ContextHandler()
    # 사용자 진행자 모드 + 출력 적게(311~316)
    ctx.set_narrator(enabled=False, user_is_narrator=True)
    ctx.set_output_level("less")
    p = ctx.build_system_prompt()
    assert "사용자는 진행자(GM) 역할" in p
    assert "이번 턴: 총 2~3줄" in p


def test_direct_and_describe_modes_and_desc_present():
    ctx = ContextHandler()
    # 진행자 설명 제공(229), 모드 direct(259~265)
    ctx.set_narrator(enabled=True, mode="active", description="테스트 진행자", user_is_narrator=False)
    ctx.set_narrator_drive("direct")
    p1 = ctx.build_system_prompt()
    assert "테스트 진행자" in p1
    assert "진행자 주도 규칙(주도형)" in p1
    assert "선택지를 제시하지 말고" in p1

    # 설명형 describe 분기(267~271)
    ctx.set_narrator_drive("describe")
    p2 = ctx.build_system_prompt()
    assert "진행자 주도 규칙(설명형)" in p2


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
