# Persona Chat 기여 가이드

기여에 관심 가져 주셔서 감사합니다. 버그 수정, 테스트 보강, 문서 개선, 기능 아이디어 — 어떤 형태든 큰 도움이 됩니다.

## 시작 전에

- **먼저 검색하세요.** 기존 이슈와 PR을 확인해서 중복 작업을 피해 주세요.
- **큰 변경 → 이슈 먼저.** 간단한 수정이 아니라면, 코드를 작성하기 전에 이슈로 범위를 맞춰 주세요.
- **작은 수정 → 바로 PR.** 오타, 문서 개선, 한두 줄 버그 수정은 이슈 없이 PR로 보내 주셔도 됩니다.

## 개발 환경 셋업

```bash
git clone https://github.com/ginishuh/persona_chatbot.git
cd persona_chatbot

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 앱 실행
python3 -m server.websocket_server
# 웹 UI  → http://127.0.0.1:9000
# WS     → ws://127.0.0.1:8765
```

AI CLI도 최소 하나는 설치·인증이 필요합니다 (Claude Code, Gemini, Droid 중 택 1). 자세한 설정은 [README](README.ko.md)를 참고하세요.

## 코드 스타일

| 영역 | 규칙 |
|------|------|
| Python 포매팅 | PEP 8, 4칸 들여쓰기, `black`·`ruff`로 자동 적용 |
| 네이밍 | 모듈/함수 `snake_case`, 클래스 `PascalCase`, 상수 `UPPER_SNAKE_CASE` |
| 타입 힌트 | 실용적인 범위에서 사용 권장 |
| 로깅 | `print` 대신 `logging` 사용 |
| JS (web/) | ES6+ (`const`/`let`), 작은 순수 함수, DOM 로직과 렌더링 분리 |
| 주석·커밋 | 한국어 기본; 식별자(변수명, 함수명)는 영어 유지 |

대부분의 규칙은 pre-commit 훅이 자동으로 잡아 줍니다.

```bash
pre-commit install          # 최초 1회
pre-commit run --all-files  # 전체 검사
```

## 테스트 실행

```bash
pytest -q                    # 단위 테스트
python scripts/ws_chat_test.py --provider claude --prompt "Smoke test"  # e2e 스모크
```

- 테스트는 `tests/` 디렉터리에 소스 구조를 미러링해서 위치합니다 (예: `tests/handlers/test_history_handler.py`).
- 파일명: `test_*.py`, 함수명: `test_*`.
- 외부 호출(CLI, 파일시스템, 네트워크)은 mock 처리. 100% 커버리지보다 의미 있는 검증을 지향합니다.

## Pull Request 제출

1. **포크 & 브랜치.** `main`에서 주제별로 브랜치를 만드세요 — 한 브랜치에 하나의 주제.
2. **작게 유지하세요.** 리뷰하기 좋은 작은 diff가 대규모 변경보다 낫습니다.
3. **문서도 갱신하세요.** 동작, 설정, 사용자 경험이 바뀌면 문서도 함께 수정해 주세요.
4. **푸시 전에 검사하세요:** `pytest -q && pre-commit run --all-files`.
5. **PR 본문을 명확히 써 주세요:** 변경 이유, 핵심 수정 내용, 검증 방법.
6. **로컬 확인.** 앱이 `:9000` / `:8765`에서 정상 동작하는지 확인 후 리뷰를 요청해 주세요.

### 커밋 메시지 형식

```
<type>(<scope>): <한국어 제목>
```

예시:
- `fix(server): WebSocket 연결 종료 시 세션 정리 누락`
- `feat(web): 토큰 사용량 표시 토글 추가`
- `docs(readme): 빠른 시작 가이드 보강`

## 버그 제보

좋은 버그 리포트에는 아래 내용이 포함됩니다.

- 기대했던 동작 vs. 실제 발생한 동작
- 재현 절차
- 환경 정보: 로컬/Docker, OS, Python 버전, AI 제공자
- 필요하면 로그, 스크린샷, 내보낸 데이터

## 기능 제안

기능 제안은 아래가 명확할수록 검토가 빨라집니다.

- 해결하려는 문제 또는 사용 사례
- 현재 한계나 우회 방법
- 기대하는 동작
- 범위나 호환성에 대한 고려 사항

## 문서 기여

README 개선, 온보딩 예시, 한영 문서 가독성 개선, 인라인 주석 정리도 모두 중요한 기여입니다. 문서 기여도 동일한 PR 프로세스를 따릅니다.

## 보안 이슈

민감한 취약점은 **공개 이슈로 등록하지 마세요.** [SECURITY.md](SECURITY.md)의 비공개 제보 절차를 따라 주세요.
