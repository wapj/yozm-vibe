"""Pydantic 모델 (PRD §6 스키마 대응)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ArticleStatus = Literal["ok", "failed"]
JobType = Literal["fetch_feed", "extract", "summarize", "rebuild_wiki"]
JobStatus = Literal["ok", "failed"]


class _RowModel(BaseModel):
    """sqlite3.Row 객체로부터 바로 만들 수 있도록 허용."""

    model_config = ConfigDict(from_attributes=True)


class Feed(_RowModel):
    id: int
    url: str
    title: str | None = None
    is_active: bool = True
    last_fetched_at: str | None = None
    consecutive_failures: int = 0
    created_at: str


class Category(_RowModel):
    id: int
    name: str
    parent_id: int | None = None
    description: str | None = None
    is_user_edited: bool = False
    merged_into_id: int | None = None
    created_at: str


class Article(_RowModel):
    id: int
    feed_id: int
    url: str
    title: str
    author: str | None = None
    published_at: str | None = None
    raw_summary: str | None = None
    extracted_content: str | None = None
    llm_summary: str | None = None
    primary_category_id: int | None = None
    language: str | None = None
    status: ArticleStatus = "ok"
    fetched_at: str


class WikiPage(_RowModel):
    id: int
    category_id: int
    content_markdown: str = ""
    last_rebuilt_at: str | None = None
    articles_count_at_rebuild: int = 0
    last_seen_at: str | None = None
    has_unread_updates: bool = False


class JobLog(_RowModel):
    id: int
    job_type: JobType
    target_ref: str | None = None
    status: JobStatus
    error_message: str | None = None
    attempt_count: int = Field(default=1, ge=1)
    started_at: str
    finished_at: str | None = None
