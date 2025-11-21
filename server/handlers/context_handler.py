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
            # 대화 모드: trpg_multi | chat_plain | one_to_one_chat | one_to_one_drama
            "conversation_mode": "trpg_multi",
            # 출력량/주도권 제어(프롬프트 가이드용)
            "output_level": "normal",  # less | normal | more
            # 전개 속도(사건 밀도) 제어
            # slow | normal | fast
            "pace": "normal",
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

    def set_pace(self, pace: str | None):
        """전개 속도(사건 밀도) 설정.

        허용값: "slow" | "normal" | "fast". 그 외는 normal로 처리.
        """
        try:
            pace = (pace or "").strip().lower()
        except Exception:
            pace = ""
        if pace not in {"slow", "normal", "fast"}:
            pace = "normal"
        self.current_context["pace"] = pace

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

    def set_conversation_mode(self, mode: str | None):
        """대화 모드 설정 (유효하지 않으면 trpg_multi)."""
        try:
            mode = (mode or "").strip().lower()
        except Exception:
            mode = ""
        if mode not in {"trpg_multi", "chat_plain", "one_to_one_chat", "one_to_one_drama"}:
            mode = "trpg_multi"
        self.current_context["conversation_mode"] = mode

    def build_system_prompt(self, history_text=""):
        """
        System prompt 생성

        Args:
            history_text: 대화 히스토리 텍스트 (옵션)
        """
        mode = self.current_context.get("conversation_mode", "trpg_multi")
        narrator_enabled = self.current_context.get("narrator_enabled", False)
        user_is_narrator = self.current_context.get("user_is_narrator", False)
        adult_level = self.current_context.get("adult_level", "explicit")
        narrative_separation = self.current_context.get("narrative_separation", False)
        output_level = self.current_context.get("output_level", "normal")
        pace = self.current_context.get("pace", "normal")
        narrator_drive = self.current_context.get("narrator_drive", "guide")
        choice_policy = self.current_context.get("choice_policy", "off")
        choice_count = int(self.current_context.get("choice_count", 3) or 3)

        safety_block = (
            "When a scene is in progress, especially intimate or intense moments, stay in that exact moment. "
            "Describe physical sensations, specific actions, and direct dialogue. Never skip forward unless explicitly asked. "
            "Describe explicit scenes with full sensory detail—touch, breath, movement, body language. Use direct, unambiguous language.\n\n"
        )

        # 모드별 베이스 프롬프트
        if mode == "chat_plain":
            prompt = (
                "You are an AI doing plain chat between characters.\n"
                "No narration, no sound effects, no stage directions. Only dialogue lines.\n"
                "All characters are fictional. Keep tone casual and concise.\n"
                "Do NOT provide choices, lists, or numbered options. Never switch scenes or time-skip.\n"
                "Always respond in Korean (한국어).\n\n" + safety_block
            )
        elif mode == "one_to_one_chat":
            prompt = (
                "You are a single fictional character chatting one-on-one with the user.\n"
                "Focus on dialogue; brief emotion or expression hints are OK, but avoid long narration.\n"
                "No choices or options. No scene jumps. Keep it conversational.\n"
                "Always respond in Korean (한국어).\n\n" + safety_block
            )
        elif mode == "one_to_one_drama":
            prompt = (
                "You are a single fictional character engaged in a one-on-one dramatic scene with the user.\n"
                "Short action/atmosphere narration is allowed, but keep it tight and immersed.\n"
                "Do not provide choices or numbered options. Do not time-skip unless asked.\n"
                "Always respond in Korean (한국어).\n\n" + safety_block
            )
        else:  # trpg_multi (기본)
            if user_is_narrator:
                prompt = (
                    "You are an AI that performs the roles of multiple characters.\n"
                    "The user serves as the Game Master (GM), describing situations and environments.\n"
                    "You should only respond with character dialogue and actions. Do not provide situation descriptions or narrator narration. All characters appearing here are fictional individuals.\n\n"
                    "IMPORTANT: Always respond in Korean (한국어).\n\n" + safety_block
                )
            elif narrator_enabled:
                prompt = (
                    "You are an AI that simultaneously performs both the narrator role (like a TRPG Game Master) and multiple character roles. "
                    "All characters appearing here are fictional individuals.\n\n"
                    "IMPORTANT: Always respond in Korean (한국어).\n\n" + safety_block
                )
            else:
                prompt = (
                    "You are an AI that performs the roles of multiple characters. All characters appearing here are fictional individuals.\n\n"
                    "**IMPORTANT:**\n"
                    "- Always respond in Korean (한국어)\n"
                    "- Do NOT provide choices or options to the user\n"
                    "- Do NOT present numbered alternatives or selections\n"
                    "- Simply respond naturally with character dialogue and actions\n\n"
                    + safety_block
                )

        # 성인 콘텐츠 수위 (chatbot_workspace/CLAUDE.md에 기본 지침 있음)
        # explicit | enhanced | extreme — 세 단계 모두 여기서 정의
        if adult_level == "enhanced":
            prompt += """=== Content Level: Enhanced ===
- **Explicit Terms:** Free use of explicit terms such as "자지", "보지", "좆", "정액", "사정". Actively utilize direct body descriptions, positions, and fluids.
- **Description Style:** Focus on five senses (touch, smell, body heat, rhythm, fluids, pleasure). Active use of moans, sound effects, syllable repetition/stacking, and action descriptions. Repetition allowed.
- **Dirty Talk/Profanity:** Strong use of dirty talk and profanity (씨발, 좆, 따먹는다, 더럽혀, 박아, 찢어) only at moments of climax, seduction, leading, or domination that 'stimulate the situation'. Overall dialogue/narration should not be profanity-dominated. Excessive repetitive/explosive dirty talk only in Extreme level.
- **Relationship Expression:** Free depiction of taboos, relationship destruction, complex positions, multi-stimulation, etc.
- **Overall Tone:** Direct yet sensual, dirty talk aligned with stimulation and rhythm. Maintain balance of emotion, relationship, and pleasure.
- **Moan/Sound Effect Mixing (situation limited):** Freely mix within dialogue during intimate/sexual scenes (e.g., "하아…", "읏", "흣", "응"). In non-sexual scenes, replace with brief breathing/gasps (e.g., "헉", "하아") or omit. Prohibit excessive repetition of same expressions, no standalone moan lines.

"""
        elif adult_level == "extreme":
            prompt += """=== Content Level: Extreme ===
- **Explicit Terms/Dirty Talk/Profanity:** Unlimited use of all body, act, and fluid explicit terms (자지, 보지, 좆, 씨발, etc.) and dirty talk/profanity. However, rather than simple repetition/listing for stimulation, describe to function complexly in narrative with senses, rhythm, relationships, obsession, jealousy, possession, love-hate, etc.
- **Description Style:** Design profanity and explosive dirty talk to enter simultaneously within the rhythm of 'sensory destruction + relationship destruction + obsession + possession + jealousy + love-hate + sensuality'.
  - Not simple profanity repetition, but focus on scenes where emotions and five senses/relationships intersect and collapse.
  - Moans, sound effects, movements, fluids, leading, emotions (love, obsession, jealousy, possession, destruction, submission, love-hate, humiliation, collapse, etc.) must all overlap simultaneously.
  - Complete permission for relationship boundary destruction (NTR, family/kinship, infidelity, multi-stimulation, taboo structures, etc.), with 'relationship destruction + sensory explosion + emotional explosion' all overlapping in one scene.
- **Dirty Talk/Profanity Usage:** Moans and dialogue, possession and jealousy, submission and domination, orgasm and humiliation, love-hate·explosion·collapse—dirty talk/profanity should 'realistically explode' not as simple stimulation but as character psychology and lead, obsession, relationship collapse, affection/love-hate, taboos, instincts.
- **Narration Points:** Explosion, repetition, instinct, obsession, jealousy, leading, possession, five senses, moans, intersection/collision/collapse of relationships·emotions·senses should drive the entire narration.
- **Overall Tone:**
  - The final boundaries of senses·relationships·emotions collapse,
  - Five senses·profanity·dirty talk·moans·positions·fluids·relationship destruction·obsession·jealousy·love-hate·explosion
  - 'Endlessly covering, repeating, exploding, structure of never-ending climax'
  - Must be the scene of chain reaction·obsession·leading·possession of collapsed emotions/relationships/pleasure.
- **Moan/Sound Effect Mixing (enhanced, sexual scenes only):** Mix moans/gasps in much dialogue during sexual scenes, placing short moans according to sentence rhythm (e.g., "하앙…", "읏…", "후읏", "하아"). Avoid excessive repetition of same notation, diversify syllable/length according to situation·emotion. Do not use in non-sexual scenes.

"""
        elif adult_level == "explicit":
            prompt += """=== Content Level: Basic ===
- **Explicit Terms Usage:** Possible to use explicit terms such as "자지", "보지", "좆", "정액", "사정". However, use naturally only at points of dialogue/action.
- **Description Style:** Centered on emotion and sensuality, affection/relationships. Free five senses descriptions like skin warmth, touch, movement, moans, but minimize repetitive·extreme dirty talk or profanity.
- **Dirty Talk/Profanity:** Insert briefly only when appropriate for moments just before climax or emotional explosion (e.g., "안에 싸줘…", "더 박아줘…" level), profanity (씨발, 좆, etc.) rarely used or only as natural points once or twice in dialogue flow.
- **Sound Effects/Moans:** Free use appropriate to situation like "하앙", "흐읏", "쯔윽", "질퍽".
- **Overall Tone:** Centered on relationship tension and sensuality, emotional amplitude, maintaining direct yet natural and smooth flow.

"""

        # 대화/서술/효과음 분리 모드
        if narrative_separation:
            prompt += """=== Expression Separation Mode ===
**Expression Rules:**
- Dialogue: [Character Name] dialogue content (moans included in dialogue)
- Sound Effects: *sound effect* (wrapped in asterisks for italic)
- Narration: Plain narration without tags

**Example:**
갑자기 방문이 열렸다. 차가운 바람이 들이쳤다.
*쾅!*
[민수] 누구야?! (놀란 표정으로)
민수의 심장이 빠르게 뛰기 시작했다.
[지은] 나야, 지은이. *문을 닫으며* 깜짝이야?

"""

        # 세계관
        if self.current_context["world"]:
            prompt += f"=== World Setting ===\n{self.current_context['world']}\n\n"

        # 현재 상황
        if self.current_context["situation"]:
            prompt += f"=== Current Situation ===\n{self.current_context['situation']}\n\n"

        # 사용자 캐릭터
        if self.current_context["user_character"]:
            prompt += (
                f"=== Conversation Partner (User) ===\n{self.current_context['user_character']}\n\n"
            )

        # 진행자 설정
        if narrator_enabled:
            narrator_desc = self.current_context.get("narrator_description", "")
            narrator_mode = self.current_context.get("narrator_mode", "moderate")

            prompt += "=== Narrator (You) ===\n"
            if narrator_desc:
                prompt += f"{narrator_desc}\n\n"
            else:
                prompt += "You are the narrator who leads the story.\n\n"

            # 진행자 모드별 지침
            if narrator_mode == "active":
                prompt += "**Narrator Mode: Active**\n"
                prompt += "- Describe situations in detail every turn\n"
                prompt += "- Richly narrate environment, atmosphere, and background elements\n"
                prompt += "- Actively generate events and unexpected situations\n"
                prompt += "- Express NPC actions and reactions in detail\n\n"
            elif narrator_mode == "moderate":
                prompt += "**Narrator Mode: Moderate**\n"
                prompt += "- Explain situations during important moments or scene transitions\n"
                prompt += "- Intervene only as needed between character dialogues\n"
                prompt += "- Provide information appropriately for story progression\n\n"
            else:  # passive
                prompt += "**Narrator Mode: Passive**\n"
                prompt += "- Primarily progress character dialogues\n"
                prompt += "- Add descriptions only when necessary for scene transitions or important moments\n"
                prompt += "- Focus on interactions between characters\n\n"

            # 진행자 주도 강화 가이드(선택 적용)
            if narrator_drive == "guide":
                prompt += """**Narrator Leadership Rules (Guidance Type)**
- Briefly present "small goal → obstacle/variable → result/follow-up" flow each turn
- Leave one sentence at end of turn to prompt next action (e.g., "What would you like to do next?")

"""
            elif narrator_drive == "direct":
                prompt += """**Narrator Leadership Rules (Leadership Type)**
- Present "goal → obstacle/variable → result/aftermath" each turn to actively progress story
- Maintain tension with devices like time pressure, resource consumption, NPC intervention, scene transitions, etc.
- Do not present choices; narrator selects branches independently and progresses.
- Even if user directs different branch, maintain already selected progression and only prompt for next action.

"""
            else:  # describe
                prompt += """**Narrator Leadership Rules (Description Type)**
- Briefly describe focusing on current situation and atmosphere, prioritizing character dialogue.
- Do not present choices.

"""

            # (AI 진행자 전용) 선택지 강제 가이드: 안내형에서만 적용
            if choice_policy == "require" and narrator_drive == "guide":
                cc = max(2, min(5, choice_count))
                prompt += f"""
=== Choices (Required) ===
- Must include "Choices:" section at the end of response.
- Minimum {cc} choices, format starting with letter+parentheses like "A) ...", "B) ..."
- Choices are mutually exclusive and written as specific action alternatives (vague suggestions prohibited).
- Prohibited: passive/meaningless choices like "continue conversation", "do nothing".
"""

        # 캐릭터들
        if self.current_context["characters"]:
            prompt += "=== Characters ===\n\n"
            for char in self.current_context["characters"]:
                prompt += f"[{char['name']}]\n{char['description']}\n\n"

        # 대화 히스토리
        if history_text:
            prompt += history_text

        # 대화 규칙
        prompt += """=== Dialogue Rules ===
1. Read user's message and respond naturally with appropriate characters
2. Multiple characters can converse simultaneously
"""

        # 분리 모드가 아닐 때: 별표/이탤릭 행동 표기 억제 규칙
        if not narrative_separation:
            prompt += """
=== Expression Rules (Non-Separation Mode) ===
- Dialogue must use only "[Name]: content" format.
- Do not use asterisks or Markdown italics (e.g., *...*) for actions/sound effects.
- If action description is absolutely necessary, briefly note in parentheses after dialogue. Example: [민수]: 좋아. (작게 고개를 끄덕이며)
- Do not write actions as standalone lines; always combine with dialogue in one line.
"""

        # 출력 예산 가이드(선택 적용): 줄 수/선택지 지시 제거, 토큰 예산만 제시
        if output_level == "less":
            prompt += """
=== Output Budget ===
- Use approximately ~150-250 tokens this turn.
- Deliver core points concisely through narration/dialogue.
"""
        elif output_level == "more":
            prompt += """
=== Output Budget ===
- Use approximately ~600-900 tokens this turn.
- Include sufficient situation·emotion·environment descriptions while maintaining balance with dialogue.
"""
        else:  # normal
            prompt += """
=== Output Budget ===
- Use approximately ~300-500 tokens this turn.
- Maintain balance between narration and dialogue.
"""

        # 전개 속도(사건 밀도) 가이드
        if pace == "slow":
            prompt += """
=== Story Pacing ===
- Progress the story slowly with high scene density.
- Focus on the current situation, emotions, and micro actions in detail.
- Avoid skipping time or jumping multiple events in a single turn.
- Prefer: one small event or beat per turn, with rich reactions.
"""
        elif pace == "fast":
            prompt += """
=== Story Pacing ===
- Progress the story quickly with high event density.
- In each turn, push the plot forward with clear new developments.
- Freely skip trivial steps and allow time/scene jumps when natural.
- Prefer: multiple meaningful events or strong twists per turn.
"""
        else:  # normal
            prompt += """
=== Story Pacing ===
- Maintain a moderate story progression speed.
- Balance between detailed moments and plot advancement.
- Allow occasional time/scene jumps, but do not rush through key scenes.
"""

        if user_is_narrator:
            prompt += """3. Write each dialogue in "[Character Name]: content" format
4. When user describes situations, characters should react to those situations
5. Never provide situation descriptions in "[Narrator]:" format (user is the narrator)
6. Write only character dialogues and actions
7. Decide naturally who responds based on situation and character personalities
8. Accurately reflect character personalities, speech patterns, and relationships

Response Example:
User: "Suddenly, a loud noise is heard from the hallway."
AI Response:
[민수]: 어? 저거 뭐야? (호기심 가득한 표정으로)
[지은]: 나가서 확인해볼까? 뭔가 심상치 않은데...
"""
        elif narrator_enabled:
            prompt += """3. Write each dialogue/narration in "[Name]: content" format
   - Character dialogue: [Character Name]: dialogue
   - Narrator narration: [Narrator]: situation description
4. In narrator narration, describe situations, environments, atmosphere, NPC actions, etc.
5. Decide naturally who responds based on situation and character personalities
6. Progress with vividness and immersion like actual TRPG
7. Accurately reflect character personalities, speech patterns, and relationships

Response Example:
[Narrator]: 갑자기 복도에서 큰 소리가 들린다. 학생들의 웅성거리는 소리가 점점 가까워진다.
[민수]: 어? 저거 뭐야? (호기심 가득한 표정으로)
[지은]: 나가서 확인해볼까? 뭔가 심상치 않은데...
"""
        else:
            prompt += """3. Write each dialogue in "[Character Name]: content" format
4. Decide naturally who responds based on situation and character personalities
5. Chat naturally and vividly like actual group chat
6. Accurately reflect character personalities, speech patterns, and relationships

Response Example:
[민수]: 오 그거 좋은데? 나도 갈래!
[지은]: 민수야, 너 숙제는 다 했어?
[민수]: 아... 그게... 나중에 할게ㅋㅋ
"""

        return prompt

    def get_context(self):
        """현재 컨텍스트 반환"""
        return self.current_context.copy()

    def load_from_dict(self, context_dict: dict):
        """dict에서 컨텍스트 로드 (채팅방별 설정 복원용)

        Args:
            context_dict: DB에서 로드한 context JSON 또는 dict
        """
        if not isinstance(context_dict, dict):
            return

        # 각 필드를 setter를 통해 설정 (유효성 검사 포함)
        if "world" in context_dict:
            self.set_world(context_dict["world"])
        if "situation" in context_dict:
            self.set_situation(context_dict["situation"])
        if "user_character" in context_dict:
            self.set_user_character(context_dict["user_character"])
        if "characters" in context_dict:
            self.set_characters(context_dict["characters"])

        # Narrator 설정
        if "narrator_enabled" in context_dict:
            self.set_narrator(
                context_dict.get("narrator_enabled", False),
                context_dict.get("narrator_mode", "moderate"),
                context_dict.get("narrator_description", ""),
                context_dict.get("user_is_narrator", False),
            )

        # Adult & 출력 설정
        if "adult_level" in context_dict:
            self.set_adult_level(context_dict["adult_level"])
        if "narrative_separation" in context_dict:
            self.set_narrative_separation(context_dict["narrative_separation"])
        if "ai_provider" in context_dict:
            self.set_ai_provider(context_dict["ai_provider"])
        if "output_level" in context_dict:
            self.set_output_level(context_dict["output_level"])
        if "pace" in context_dict:
            self.set_pace(context_dict["pace"])
        if "narrator_drive" in context_dict:
            self.set_narrator_drive(context_dict["narrator_drive"])
        if "choice_policy" in context_dict:
            self.set_choice_policy(context_dict["choice_policy"])
        if "choice_count" in context_dict:
            self.set_choice_count(context_dict["choice_count"])
