from server.handlers.token_usage_handler import TokenUsageHandler


def make_token_info(i, o, cr=0, cc=0):
    return {
        "input_tokens": i,
        "output_tokens": o,
        "cache_read_tokens": cr,
        "cache_creation_tokens": cc,
    }


def test_add_and_get_and_clear_usage():
    tuh = TokenUsageHandler()
    tuh.add_usage("s1", "r1", "claude", None)  # no-op

    tuh.add_usage("s1", "r1", "claude", make_token_info(10, 5))
    tuh.add_usage("s1", "r1", "claude", make_token_info(3, 2))

    usage = tuh.get_usage("s1", "r1")
    assert "claude" in usage
    assert usage["claude"]["message_count"] == 2

    # formatted summary
    summary = tuh.get_formatted_summary("s1", "r1")
    assert summary["providers"]["claude"]["supported"] is True
    assert summary["providers"]["gemini"]["supported"] is False

    # clear single room
    tuh.clear_usage("s1", "r1")
    assert tuh.get_usage("s1", "r1") == {}

    # refill and clear session
    tuh.add_usage("s1", "r2", "droid", make_token_info(1, 1))
    tuh.clear_usage("s1")
    assert tuh.get_usage("s1", "r2") == {}
