from rss_wiki.ingest.failures import FAILURE_THRESHOLD, is_failing


def test_is_failing_below_threshold_returns_false():
    assert is_failing(4) is False


def test_is_failing_at_threshold_returns_true():
    assert is_failing(5) is True


def test_is_failing_respects_custom_threshold():
    assert is_failing(3, threshold=3) is True
    assert is_failing(2, threshold=3) is False
