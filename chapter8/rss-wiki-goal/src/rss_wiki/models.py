"""Pydantic 모델 및 dataclass."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Feed:
    id: Optional[int]
    url: str
    title: Optional[str] = None
    is_active: bool = True
    last_fetched_at: Optional[str] = None
    consecutive_failures: int = 0
    created_at: Optional[str] = None


@dataclass
class Category:
    id: Optional[int]
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None
    is_user_edited: bool = False
    merged_into_id: Optional[int] = None
    created_at: Optional[str] = None


@dataclass
class Article:
    id: Optional[int]
    feed_id: int
    url: str
    title: str
    author: Optional[str] = None
    published_at: Optional[str] = None
    raw_summary: Optional[str] = None
    extracted_content: Optional[str] = None
    llm_summary: Optional[str] = None
    primary_category_id: Optional[int] = None
    language: Optional[str] = None
    status: str = "ok"
    fetched_at: Optional[str] = None


@dataclass
class WikiPage:
    id: Optional[int]
    category_id: int
    content_markdown: str = ""
    last_rebuilt_at: Optional[str] = None
    articles_count_at_rebuild: int = 0
    last_seen_at: Optional[str] = None
    has_unread_updates: bool = False


@dataclass
class JobLog:
    id: Optional[int]
    job_type: str
    status: str
    started_at: str
    target_ref: Optional[str] = None
    error_message: Optional[str] = None
    attempt_count: int = 1
    finished_at: Optional[str] = None


@dataclass
class LLMSummaryResult:
    summary: str
    category_name: str
    is_new_category: bool
    language_detected: str


@dataclass
class ArticleContext:
    """위키 재구성 시 기존 글 컨텍스트용."""
    title: str
    published_at: Optional[str]
    one_line: str


@dataclass
class NewArticleForWiki:
    """위키 재구성 입력용 신규 글."""
    title: str
    url: str
    llm_summary: Optional[str]
    published_at: Optional[str]
