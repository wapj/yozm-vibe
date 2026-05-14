import textwrap
import pytest
from pathlib import Path

from rss_wiki.config import FeedConfig, load_feeds


def write_toml(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "feeds.toml"
    p.write_text(textwrap.dedent(content))
    return p


def test_load_feeds_normal(tmp_path):
    toml_file = write_toml(tmp_path, """
        [[feed]]
        name = "Hacker News Front Page"
        url  = "https://hnrss.org/frontpage"

        [[feed]]
        name = "Python Insider"
        url  = "https://feeds.feedburner.com/PythonInsider"
    """)
    feeds = load_feeds(toml_file)
    assert len(feeds) == 2
    assert all(isinstance(f, FeedConfig) for f in feeds)
    assert feeds[0].name == "Hacker News Front Page"
    assert feeds[0].url == "https://hnrss.org/frontpage"
    assert feeds[1].name == "Python Insider"


def test_load_feeds_empty_file(tmp_path):
    toml_file = write_toml(tmp_path, "")
    with pytest.raises(ValueError, match="No \\[\\[feed\\]\\] entries"):
        load_feeds(toml_file)


def test_load_feeds_missing_url(tmp_path):
    toml_file = write_toml(tmp_path, """
        [[feed]]
        name = "No URL Feed"
    """)
    with pytest.raises(ValueError, match="url"):
        load_feeds(toml_file)
