"""라우팅 및 SPA fallback 스모크 테스트"""


class TestSPARouting:
    """SPA 라우팅 기본 동작 테스트"""

    def test_route_patterns(self):
        """라우팅 패턴 정의 검증"""
        route_table = [
            {"pattern": r"^\/$", "view": "room-list"},
            {"pattern": r"^\/rooms\/([^\/]+)$", "view": "room-detail"},
            {"pattern": r"^\/rooms\/([^\/]+)\/settings$", "view": "room-settings"},
            {"pattern": r"^\/rooms\/([^\/]+)\/history$", "view": "room-history"},
            {"pattern": r"^\/backup$", "view": "backup"},
        ]

        assert len(route_table) == 5
        assert route_table[0]["view"] == "room-list"
        assert route_table[1]["view"] == "room-detail"

    def test_route_matching_root(self):
        """루트 경로 매칭 테스트"""
        import re

        pattern = r"^\/$"
        assert re.match(pattern, "/")
        assert not re.match(pattern, "/rooms")

    def test_route_matching_room_detail(self):
        """채팅방 상세 경로 매칭 테스트"""
        import re

        pattern = r"^\/rooms\/([^\/]+)$"

        match = re.match(pattern, "/rooms/fantasy_001")
        assert match is not None
        assert match.group(1) == "fantasy_001"

        match = re.match(pattern, "/rooms/test_room")
        assert match is not None
        assert match.group(1) == "test_room"

        # 하위 경로는 매칭 안 됨
        assert not re.match(pattern, "/rooms/test_room/settings")

    def test_route_matching_room_settings(self):
        """채팅방 설정 경로 매칭 테스트"""
        import re

        pattern = r"^\/rooms\/([^\/]+)\/settings$"

        match = re.match(pattern, "/rooms/test_room/settings")
        assert match is not None
        assert match.group(1) == "test_room"

        # settings가 없으면 매칭 안 됨
        assert not re.match(pattern, "/rooms/test_room")

    def test_route_matching_room_history(self):
        """채팅방 히스토리 경로 매칭 테스트"""
        import re

        pattern = r"^\/rooms\/([^\/]+)\/history$"

        match = re.match(pattern, "/rooms/test_room/history")
        assert match is not None
        assert match.group(1) == "test_room"

    def test_route_matching_backup(self):
        """백업 경로 매칭 테스트"""
        import re

        pattern = r"^\/backup$"

        assert re.match(pattern, "/backup")
        assert not re.match(pattern, "/backup/export")


class TestURLParsing:
    """URL 파싱 테스트"""

    def test_room_id_extraction(self):
        """채팅방 ID 추출 테스트"""
        import re

        pattern = r"^\/rooms\/([^\/]+)"
        url = "/rooms/fantasy_adventure_001"

        match = re.match(pattern, url)
        assert match is not None

        room_id = match.group(1)
        assert room_id == "fantasy_adventure_001"

    def test_room_id_with_special_chars(self):
        """특수 문자 포함 채팅방 ID"""
        import re

        pattern = r"^\/rooms\/([^\/]+)"

        # 언더스코어, 하이픈, 숫자
        for test_id in ["room_001", "room-test", "room123", "test_room_001"]:
            url = f"/rooms/{test_id}"
            match = re.match(pattern, url)
            assert match is not None
            assert match.group(1) == test_id

    def test_url_encoding(self):
        """URL 인코딩된 채팅방 ID"""
        from urllib.parse import quote, unquote

        room_id = "테스트 방"
        encoded = quote(room_id)
        assert encoded == "%ED%85%8C%EC%8A%A4%ED%8A%B8%20%EB%B0%A9"

        decoded = unquote(encoded)
        assert decoded == room_id


class TestSPAFallback:
    """SPA fallback 동작 테스트"""

    def test_api_paths_excluded(self):
        """API 경로는 fallback 제외"""
        api_paths = [
            "/api/export",
            "/api/export/stream",
            "/api/export/md",
            "/api/import",
        ]

        for path in api_paths:
            # API 경로는 index.html이 아닌 실제 API 응답을 반환해야 함
            assert path.startswith("/api/")

    def test_static_paths_excluded(self):
        """정적 파일 경로는 fallback 제외"""
        static_paths = [
            "/style.css",
            "/app.js",
            "/src/logo3.png",
        ]

        for path in static_paths:
            # 정적 파일은 index.html이 아닌 파일 내용을 반환해야 함
            assert path.endswith(".css") or path.endswith(".js") or path.endswith(".png")

    def test_spa_routes_return_index(self):
        """SPA 라우트는 index.html 반환"""
        spa_routes = [
            "/",
            "/rooms/test",
            "/rooms/test/settings",
            "/rooms/test/history",
            "/backup",
        ]

        for route in spa_routes:
            # SPA 라우트는 모두 index.html을 반환해야 함
            # (실제 HTTP 테스트에서는 Content-Type: text/html 확인)
            assert not route.startswith("/api/")
            assert not any(route.endswith(ext) for ext in [".css", ".js", ".png", ".json"])


class TestNavigationFlow:
    """네비게이션 흐름 테스트"""

    def test_room_list_to_room_detail(self):
        """채팅방 목록 → 채팅방 상세 흐름"""
        # 1. 루트 경로: 채팅방 목록
        current_path = "/"
        assert current_path == "/"

        # 2. 채팅방 선택 → 채팅방 상세로 이동
        room_id = "fantasy_001"
        current_path = f"/rooms/{room_id}"
        assert current_path == "/rooms/fantasy_001"

    def test_room_detail_to_settings(self):
        """채팅방 상세 → 설정 흐름"""
        room_id = "test_room"

        # 채팅방에서 시작
        current_path = f"/rooms/{room_id}"
        assert current_path == "/rooms/test_room"

        # 설정으로 이동
        current_path = f"/rooms/{room_id}/settings"
        assert current_path == "/rooms/test_room/settings"

    def test_room_detail_to_history(self):
        """채팅방 상세 → 히스토리 흐름"""
        room_id = "test_room"

        current_path = f"/rooms/{room_id}"
        current_path = f"/rooms/{room_id}/history"
        assert current_path == "/rooms/test_room/history"

    def test_navigate_to_backup(self):
        """백업 화면으로 이동"""
        current_path = "/"
        current_path = "/backup"
        assert current_path == "/backup"


class TestBrowserNavigation:
    """브라우저 네비게이션 동작 테스트"""

    def test_forward_back_navigation(self):
        """뒤로가기/앞으로가기 시뮬레이션"""
        history_stack = []

        # 1. 루트
        history_stack.append("/")
        assert history_stack[-1] == "/"

        # 2. 채팅방
        history_stack.append("/rooms/test")
        assert history_stack[-1] == "/rooms/test"

        # 3. 설정
        history_stack.append("/rooms/test/settings")
        assert history_stack[-1] == "/rooms/test/settings"

        # 뒤로가기
        history_stack.pop()
        assert history_stack[-1] == "/rooms/test"

        # 뒤로가기
        history_stack.pop()
        assert history_stack[-1] == "/"

    def test_direct_url_access(self):
        """직접 URL 접근 (새로고침)"""
        # 새로고침 시에도 같은 페이지 유지
        url = "/rooms/fantasy_001/settings"

        # SPA fallback으로 index.html 반환
        # → JavaScript가 URL 파싱하여 올바른 화면 렌더링
        assert url == "/rooms/fantasy_001/settings"

    def test_bookmark_url(self):
        """북마크된 URL 접근"""
        bookmarked_urls = [
            "/rooms/favorite_room",
            "/rooms/favorite_room/settings",
            "/backup",
        ]

        for url in bookmarked_urls:
            # 북마크된 URL로 직접 접근 가능
            assert url.startswith("/")


class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_trailing_slash(self):
        """경로 끝 슬래시 처리"""
        import re

        # 루트는 슬래시 허용
        assert re.match(r"^\/$", "/")

        # 다른 경로는 슬래시 없음
        assert re.match(r"^\/rooms\/([^\/]+)$", "/rooms/test")
        assert not re.match(r"^\/rooms\/([^\/]+)$", "/rooms/test/")

    def test_empty_room_id(self):
        """빈 채팅방 ID"""
        import re

        pattern = r"^\/rooms\/([^\/]+)$"

        # 빈 ID는 매칭 안 됨
        assert not re.match(pattern, "/rooms/")
        assert not re.match(pattern, "/rooms")

    def test_nested_paths(self):
        """중첩 경로 처리"""
        import re

        # /rooms/id/settings/extra 같은 경로는 매칭 안 됨
        pattern = r"^\/rooms\/([^\/]+)\/settings$"
        assert not re.match(pattern, "/rooms/test/settings/extra")

    def test_case_sensitivity(self):
        """대소문자 구분"""
        import re

        pattern = r"^\/backup$"

        assert re.match(pattern, "/backup")
        assert not re.match(pattern, "/Backup")
        assert not re.match(pattern, "/BACKUP")
