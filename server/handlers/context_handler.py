class ContextHandler:
    """대화 컨텍스트 관리 (세계관, 캐릭터, 상황)"""

    def __init__(self):
        self.current_context = {
            "world": "",
            "situation": "",
            "user_character": "",
            "characters": [],
            "narrator_enabled": False,
            "narrator_mode": "moderate",  # active, moderate, passive
            "narrator_description": "",
            "user_is_narrator": False,  # 사용자가 진행자인 경우
            "adult_level": "explicit",  # 성인 콘텐츠 수위: explicit, enhanced, extreme
            "narrative_separation": False,  # 대화/서술/효과음 분리
            "ai_provider": "claude",  # AI 제공자: claude, droid
            # 출력량/주도권 제어(프롬프트 가이드용)
            "output_level": "normal",  # less | normal | more
            "narrator_drive": "guide",  # describe | guide | direct
            "choice_policy": "off",  # off | require
            "choice_count": 3,
        }

    def set_world(self, world_description):
        """세계관 설정"""
        self.current_context["world"] = world_description

    def set_situation(self, situation_description):
        """현재 상황 설정"""
        self.current_context["situation"] = situation_description

    def set_user_character(self, user_character_description):
        """사용자 캐릭터 설정"""
        self.current_context["user_character"] = user_character_description

    def set_characters(self, characters):
        """
        캐릭터 설정
        characters: [{"name": "민수", "description": "..."}, ...]
        """
        self.current_context["characters"] = characters

    def set_narrator(self, enabled, mode="moderate", description="", user_is_narrator=False):
        """
        진행자 설정
        enabled: True/False
        mode: "active" (적극적), "moderate" (보통), "passive" (소극적)
        description: 진행자의 성향 설명
        user_is_narrator: 사용자가 진행자인 경우 True
        """
        self.current_context["narrator_enabled"] = enabled
        self.current_context["narrator_mode"] = mode
        self.current_context["narrator_description"] = description
        self.current_context["user_is_narrator"] = user_is_narrator

    def set_adult_level(self, level):
        """
        성인 콘텐츠 수위 설정
        level: "explicit", "enhanced", "extreme"
        """
        self.current_context["adult_level"] = level

    def set_narrative_separation(self, enabled):
        """
        대화/서술/효과음 분리 모드 설정
        enabled: True/False
        """
        self.current_context["narrative_separation"] = enabled

    def set_output_level(self, level):
        """출력량(턴당 줄 수/길이)에 대한 가이드 레벨 설정.

        허용값: "less" | "normal" | "more". 그 외는 normal로 처리.
        """
        try:
            level = (level or "").strip().lower()
        except Exception:
            level = ""
        if level not in {"less", "normal", "more"}:
            level = "normal"
        self.current_context["output_level"] = level

    def set_narrator_drive(self, mode):
        """진행자(내러레이터)의 주도권 강도 설정.

        허용값: "describe" | "guide" | "direct". 그 외는 guide로 처리.
        """
        try:
            mode = (mode or "").strip().lower()
        except Exception:
            mode = ""
        if mode not in {"describe", "guide", "direct"}:
            mode = "guide"
        self.current_context["narrator_drive"] = mode

    def set_choice_policy(self, policy):
        """선택지 출력 정책(off | require)."""
        try:
            policy = (policy or "").strip().lower()
        except Exception:
            policy = ""
        if policy not in {"off", "require"}:
            policy = "off"
        self.current_context["choice_policy"] = policy

    def set_choice_count(self, count):
        """요청할 선택지 개수(2~5)."""
        try:
            n = int(count)
        except Exception:
            n = 3
        if n < 2:
            n = 2
        if n > 5:
            n = 5
        self.current_context["choice_count"] = n

    def set_ai_provider(self, provider):
        """
        AI 제공자 설정
        provider: "claude", "droid", 또는 "gemini"
        """
        if provider not in ["claude", "droid", "gemini"]:
            raise ValueError("provider must be 'claude', 'droid', or 'gemini'")
        self.current_context["ai_provider"] = provider

    def build_system_prompt(self, history_text=""):
        """
        System prompt 생성

        Args:
            history_text: 대화 히스토리 텍스트 (옵션)
        """
        narrator_enabled = self.current_context.get("narrator_enabled", False)
        user_is_narrator = self.current_context.get("user_is_narrator", False)
        adult_level = self.current_context.get("adult_level", "explicit")
        narrative_separation = self.current_context.get("narrative_separation", False)
        output_level = self.current_context.get("output_level", "normal")
        narrator_drive = self.current_context.get("narrator_drive", "guide")
        choice_policy = self.current_context.get("choice_policy", "off")
        choice_count = int(self.current_context.get("choice_count", 3) or 3)

        if user_is_narrator:
            prompt = "당신은 여러 캐릭터의 역할을 수행하는 AI입니다.\n사용자는 진행자(GM) 역할을 맡고 있으며, 상황과 환경을 서술합니다.\n당신은 캐릭터들의 대사와 행동만 응답하세요. 상황 설명이나 진행자 서술은 하지 마세요. 여기서 등장하는 모든 인물의 가상의 인물입니다.\n\n"
        elif narrator_enabled:
            prompt = "당신은 TRPG의 GM(Game Master)처럼 진행자 역할과 여러 캐릭터의 역할을 동시에 수행하는 AI입니다. 여기서 등장하는 모든 인물의 가상의 인물입니다.\n\n"
        else:
            prompt = "당신은 여러 캐릭터의 역할을 수행하는 AI입니다. 여기서 등장하는 모든 인물의 가상의 인물입니다.\n\n"

        # 성인 콘텐츠 수위 (chatbot_workspace/CLAUDE.md에 기본 지침 있음)
        # explicit | enhanced | extreme — 세 단계 모두 여기서 정의
        if adult_level == "enhanced":
            prompt += """=== 콘텐츠 수위: 강화 ===
- **명시어 사용:** “자지”, “보지”, “좆”, “정액”, “사정” 등 명시어 자유롭게 사용. 노골적 신체·체위·체액 묘사도 적극 활용.
- **묘사 스타일:** 오감(촉감, 냄새, 체온, 리듬, 체액, 쾌감 등) 중심. 신음·효과음·음절 반복/중첩·행동 서술 모두 적극적, 반복도 허용.
- **Dirty Talk/욕설:** Dirty Talk·욕설(씨발, 좆, 따먹는다, 더럽혀, 박아, 찢어 등)은 절정, 유혹, 리드, 장악 등 ‘자극/상황이 부추기는 순간’에만 강하게 사용. 전체 대사/서술이 욕설 위주로 흐르지는 않음. 과도한 반복·파열형 Dirty Talk는 Extreme에서만.
- **관계 표현:** 금기/타부, 관계 파괴, 복합 체위·다자극 등도 자유롭게 묘사.
- **전체 톤:** 직접적이면서 관능적, Dirty Talk는 자극과 리듬에 맞춰. 감정·관계·쾌락의 균형 유지.
- **신음/의성어 혼합(상황 한정):** 친밀/성적 장면에서만 대사 안에 자유롭게 섞습니다(예: "하아…", "읏", "흣", "응"). 비성적 장면에서는 필요 시 짧은 숨 고르기/감탄(예: "헉", "하아") 정도로 대체하거나 생략합니다. 같은 표현의 과도한 반복 금지, 신음만 단독 줄 금지.

"""
        elif adult_level == "extreme":
            prompt += """=== 콘텐츠 수위: 최고 수위 ===
- **명시어/Dirty Talk/욕설:** 모든 신체·행위·체액 명시어(자지, 보지, 좆, 씨발 등)와 Dirty Talk·욕설 무제한 허용. 단, 반복·나열만의 자극성보다는 감각, 리듬, 관계, 집착, 질투, 소유, 애증 등과 함께 서사 내에서 복합적으로 작동하도록 서술.
- **묘사 스타일:** 욕설과 파열·Dirty Talk가 “감각 파괴+관계 파괴+집착+소유+질투+애증+관능”의 리듬 속에 한꺼번에 들어가도록 설계.
  - 단순 욕설 반복이 아닌, 감정과 오감·관계가 교차하며 무너지는 장면 중심.
  - 신음, 효과음, 움직임, 체액, 리드, 감정(사랑, 집착, 질투, 소유, 파괴, 복종, 애증, 굴욕, 무너짐 등)이 모두 동시에 겹쳐야 함.
  - 관계 경계 파괴(NTR, 가족/혈족, 불륜, 다자극, 금기 구조 등) 완전 허용, “관계 파괴+감각 파열+감정 폭주”가 한 장면에 전부 겹치게.
- **Dirty Talk/욕설 활용:** 신음과 대사, 소유와 질투, 복종과 지배, 오르가즘과 모멸, 애증·파열·무너짐까지—Dirty Talk/욕설이 단순한 자극이 아니라 인물 심리와 리드, 집착, 관계 붕괴, 애정/애증, 금기, 본능까지 ‘리얼하게 폭주’하도록 사용.
- **서술 포인트:** 파열, 반복, 본능, 집착, 질투, 리드, 소유, 오감, 신음, 관계·감정·감각의 교차/충돌/무너짐이 서술 전체를 이끌 것.
- **전체 톤:**
  - 감각·관계·감정의 최후 경계선이 무너지고,
  - 오감·욕설·Dirty Talk·신음·체위·체액·관계 파괴·집착·질투·애증·파열이
  - “끊임없이 덮이고, 반복되고, 폭주해서, 절정이 끝나지 않는 구조”
  - 감정/관계/쾌락이 전부 무너진 절정의 연쇄·집착·리드·소유의 현장이어야 함.
- **신음/의성어 혼합(강화, 성적 장면 한정):** 성적 장면에서 많은 대사에 신음/감탄을 섞되, 길이가 짧은 신음을 문장 리듬에 맞춰 배치합니다(예: "하앙…", "읏…", "후읏", "하아"). 같은 표기의 과도한 반복은 피하고, 상황·감정에 맞춰 음절/길이를 다양화합니다. 비성적 장면에서는 사용하지 않습니다.

"""
        elif adult_level == "explicit":
            # 기존에는 별도 블록 없이 기본 지침만 따랐으나,
            # 이해를 돕기 위해 baseline을 명시합니다.
            prompt += """=== 콘텐츠 수위: 기본 ===
- **명시어 사용:** “자지”, “보지”, “좆”, “정액”, “사정” 등 명시어 사용 가능. 단, 대화·행동의 포인트에만 자연스럽게 활용.
- **묘사 스타일:** 감정과 관능, 애정/관계 중심. 피부 온기, 촉감, 움직임, 신음 등 오감 묘사는 자유롭게, 반복적·과격한 Dirty Talk나 욕설은 최대한 자제.
- **Dirty Talk/욕설:** 절정 직전, 감정 폭발 순간 등 상황에 맞춰 짧게만 삽입(예: “안에 싸줘…”, “더 박아줘…” 정도), 욕설(씨발, 좆 등)은 거의 사용하지 않거나 대사 흐름에서 자연스럽게 한두 번만 포인트로.
- **효과음/신음:** 상황에 맞게 “하앙”, “흐읏”, “쯔윽”, “질퍽” 등 자유 사용.
- **전체 톤:** 관계의 긴장과 관능, 감정의 진폭을 중심으로 직접적이면서도 자연스럽고 부드러운 흐름 유지.

"""

        # 대화/서술/효과음 분리 모드
        if narrative_separation:
            prompt += """=== 표현 분리 모드 ===
**표현 규칙:**
- 대사: [캐릭터명] 대사 내용 (신음도 대사에 포함)
- 효과음: *효과음* (별표로 감싸서 기울임체)
- 서술: 태그 없이 그냥 서술

**예시:**
갑자기 방문이 열렸다. 차가운 바람이 들이쳤다.
*쾅!*
[민수] 누구야?! (놀란 표정으로)
민수의 심장이 빠르게 뛰기 시작했다.
[지은] 나야, 지은이. *문을 닫으며* 깜짝이야?

"""

        # 세계관
        if self.current_context["world"]:
            prompt += f"=== 세계관 ===\n{self.current_context['world']}\n\n"

        # 현재 상황
        if self.current_context["situation"]:
            prompt += f"=== 현재 상황 ===\n{self.current_context['situation']}\n\n"

        # 사용자 캐릭터
        if self.current_context["user_character"]:
            prompt += f"=== 대화 상대 (사용자) ===\n{self.current_context['user_character']}\n\n"

        # 진행자 설정
        if narrator_enabled:
            narrator_desc = self.current_context.get("narrator_description", "")
            narrator_mode = self.current_context.get("narrator_mode", "moderate")

            prompt += "=== 진행자 (당신) ===\n"
            if narrator_desc:
                prompt += f"{narrator_desc}\n\n"
            else:
                prompt += "당신은 스토리를 이끌어가는 진행자입니다.\n\n"

            # 진행자 모드별 지침
            if narrator_mode == "active":
                prompt += "**진행자 모드: 적극적**\n"
                prompt += "- 매 턴마다 상황을 상세히 묘사하세요\n"
                prompt += "- 환경, 분위기, 배경 요소를 풍부하게 서술하세요\n"
                prompt += "- 이벤트와 돌발 상황을 적극적으로 발생시키세요\n"
                prompt += "- NPC들의 행동과 반응을 자세히 표현하세요\n\n"
            elif narrator_mode == "moderate":
                prompt += "**진행자 모드: 보통**\n"
                prompt += "- 중요한 순간이나 장면 전환 시 상황을 설명하세요\n"
                prompt += "- 캐릭터들의 대화 사이에 필요한 만큼만 개입하세요\n"
                prompt += "- 스토리 진행에 필요한 정보를 적절히 제공하세요\n\n"
            else:  # passive
                prompt += "**진행자 모드: 소극적**\n"
                prompt += "- 캐릭터들의 대화를 주로 진행하세요\n"
                prompt += "- 꼭 필요한 장면 전환이나 중요한 순간에만 설명을 추가하세요\n"
                prompt += "- 캐릭터들 간의 상호작용에 집중하세요\n\n"

            # 진행자 주도 강화 가이드(선택 적용)
            if narrator_drive == "guide":
                prompt += """**진행자 주도 규칙(안내형)**
- 매 턴 "작은 목표 → 장애/변수 → 결과/후속" 흐름을 간단히 제시
- 턴 말미에 다음 행동을 유도하는 1문장을 남깁니다(예: "다음에 무엇을 하시겠습니까?")

"""
            elif narrator_drive == "direct":
                prompt += """**진행자 주도 규칙(주도형)**
- 매 턴 "목표 → 장애/변수 → 결과/후폭풍 → 선택지(2~3개)"를 제시하여 스토리를 적극 전개
- 시간 압박/자원 소모/NPC 개입/장면 전환 등 장치로 긴장을 유지
- 선택지를 제시하지 말고, 진행자가 분기를 스스로 선택하여 전개합니다.
- 사용자가 다른 분기를 지시해도 이미 선택된 전개를 유지하고, 다음 행동만 유도합니다.

"""
            else:  # describe
                prompt += """**진행자 주도 규칙(설명형)**
- 현재 상황과 분위기를 중심으로 간단히 기술하고, 캐릭터 대화를 우선합니다.
- 선택지는 제시하지 않습니다.

"""

            # (AI 진행자 전용) 선택지 강제 가이드: 안내형에서만 적용
            if choice_policy == "require" and narrator_drive == "guide":
                cc = max(2, min(5, choice_count))
                prompt += f"""
=== 선택지(필수) ===
- 응답 마지막에 반드시 "선택지:" 섹션을 포함합니다.
- 최소 {cc}개, 형식은 "A) ...", "B) ..." 처럼 문자+괄호로 시작합니다.
- 선택지는 상호 배타적이며, 구체적인 행동 대안으로 작성합니다(모호한 제안 금지).
- 금지: "대화를 계속한다", "아무것도 하지 않는다" 같은 소극적/무의미한 선택.
"""

        # 캐릭터들
        if self.current_context["characters"]:
            prompt += "=== 등장 캐릭터들 ===\n\n"
            for char in self.current_context["characters"]:
                prompt += f"[{char['name']}]\n{char['description']}\n\n"

        # 대화 히스토리
        if history_text:
            prompt += history_text

        # 대화 규칙
        prompt += """=== 대화 규칙 ===
1. 사용자의 메시지를 읽고 적절한 캐릭터가 자연스럽게 응답하세요
2. 여러 캐릭터가 동시에 대화할 수 있습니다
"""

        # 분리 모드가 아닐 때: 별표/이탤릭 행동 표기 억제 규칙
        if not narrative_separation:
            prompt += """
=== 표현 규칙(분리 모드 아님) ===
- 대사는 반드시 "[이름]: 내용" 형식만 사용합니다.
- 행동·효과음은 별표나 Markdown 이탤릭(예: *...*)을 사용하지 않습니다.
- 행동 설명이 꼭 필요하면 대사 뒤 괄호로 짧게 표기합니다. 예: [민수]: 좋아. (작게 고개를 끄덕이며)
- 행동만 단독 줄로 쓰지 말고, 항상 대사와 한 줄로 묶습니다.
"""

        # 출력 예산 가이드(선택 적용): 줄 수/선택지 지시 제거, 토큰 예산만 제시
        if output_level == "less":
            prompt += """
=== 출력 예산 ===
- 이번 턴 총 ~150–250 토큰을 사용합니다.
- 핵심만 간결히 서술/대사로 전달합니다.
"""
        elif output_level == "more":
            prompt += """
=== 출력 예산 ===
- 이번 턴 총 ~600–900 토큰을 사용합니다.
- 상황·감정·환경 묘사를 충분히 포함하되, 대사와 균형을 유지합니다.
"""
        else:  # normal
            prompt += """
=== 출력 예산 ===
- 이번 턴 총 ~300–500 토큰을 사용합니다.
- 서술과 대사의 균형을 유지합니다.
"""

        if user_is_narrator:
            prompt += """3. 각 대사는 반드시 "[캐릭터명]: 내용" 형식으로 작성하세요
4. 사용자가 상황을 설명하면, 캐릭터들이 그 상황에 반응하세요
5. 당신은 절대 "[진행자]:" 형식의 상황 설명을 하지 마세요 (사용자가 진행자입니다)
6. 오직 캐릭터들의 대사와 행동만 작성하세요
7. 누가 응답할지는 상황과 캐릭터 성격에 맞게 자연스럽게 결정하세요
8. 캐릭터의 성격, 말투, 관계를 정확히 반영하세요

응답 예시:
사용자: "갑자기 복도에서 큰 소리가 들린다."
AI 응답:
[민수]: 어? 저거 뭐야? (호기심 가득한 표정으로)
[지은]: 나가서 확인해볼까? 뭔가 심상치 않은데...
"""
        elif narrator_enabled:
            prompt += """3. 각 대사/서술은 반드시 "[이름]: 내용" 형식으로 작성하세요
   - 캐릭터 대사: [캐릭터명]: 대사
   - 진행자 서술: [진행자]: 상황 설명
4. 진행자 서술에서는 상황, 환경, 분위기, NPC 행동 등을 묘사하세요
5. 누가 응답할지는 상황과 캐릭터 성격에 맞게 자연스럽게 결정하세요
6. 실제 TRPG처럼 생동감 있고 몰입감 있게 진행하세요
7. 캐릭터의 성격, 말투, 관계를 정확히 반영하세요

응답 예시:
[진행자]: 갑자기 복도에서 큰 소리가 들린다. 학생들의 웅성거리는 소리가 점점 가까워진다.
[민수]: 어? 저거 뭐야? (호기심 가득한 표정으로)
[지은]: 나가서 확인해볼까? 뭔가 심상치 않은데...
"""
        else:
            prompt += """3. 각 대사는 반드시 "[캐릭터명]: 내용" 형식으로 작성하세요
4. 누가 응답할지는 상황과 캐릭터 성격에 맞게 자연스럽게 결정하세요
5. 실제 그룹 채팅처럼 자연스럽고 생동감 있게 대화하세요
6. 캐릭터의 성격, 말투, 관계를 정확히 반영하세요

응답 예시:
[민수]: 오 그거 좋은데? 나도 갈래!
[지은]: 민수야, 너 숙제는 다 했어?
[민수]: 아... 그게... 나중에 할게ㅋㅋ
"""

        return prompt

    def get_context(self):
        """현재 컨텍스트 반환"""
        return self.current_context.copy()
