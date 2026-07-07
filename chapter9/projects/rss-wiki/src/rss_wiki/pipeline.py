"""`fetch`의 순수 오케스트레이션 계층: 피드/글 루프, 실패 스킵, state 적재, 실행 리포트.

파일 시스템·네트워크·프로세스에 의존하지 않는다. 실제 파일 쓰기(`wiki.write_wiki`),
`state.json` 저장, 종료 코드 매핑, stdout 출력은 T13(CLI) 범위다.
"""

from __future__ import annotations

import asyncio

from rss_wiki import ingest
from rss_wiki import extract as extract_module
from rss_wiki import summarize as summarize_module
from rss_wiki import wiki


def _existing_filenames(state: dict) -> set[str]:
    return {
        record["meta"]["filename"]
        for record in state.get("processed", {}).values()
        if "meta" in record and "filename" in record["meta"]
    }


def run_fetch(
    feeds: list[dict],
    state: dict,
    *,
    limit: int,
    now: str,
    collected_date: str,
    select=ingest.select_new_articles,
    extract=extract_module.extract_body,
    summarize=summarize_module.summarize_article,
) -> dict:
    """전체 피드를 순회해 새 글을 수집→본문 확보→요약하고 결과를 모아 반환한다.

    반환 dict는 다음 3개 키를 담는다.
      - "batch": 이번 배치에서 성공한 글 목록. 각 항목은
        `{"summary_result", "collected_date", "filename"}`로, T13이
        `wiki.write_wiki`에 넘길 입력이다.
      - "state": 성공한 글만 `processed[id] = {processed_at, status, meta}`로
        추가 적재된 새 state(입력 `state`는 변경하지 않는다).
      - "report": 피드/글 단위 성공·실패 건수와 실패 사유를 담은 실행 리포트.

    피드 단위 실패(`ingest.FeedParseError`)는 해당 피드를 건너뛰고 다음 피드로
    계속한다. 글 단위 실패(`extract.ArticleExtractionError`/
    `summarize.SummarizeError`)는 해당 글을 건너뛰고(state에 기록하지 않아
    다음 `fetch`에서 재시도됨) 같은 피드의 다른 글 처리를 계속한다(PRD 7).
    """
    new_state = {**state, "processed": dict(state.get("processed", {}))}
    existing_filenames = _existing_filenames(state)

    report = {
        "feeds": {"succeeded": 0, "failed": 0, "failures": []},
        "articles": {"succeeded": 0, "failed": 0, "failures": []},
    }
    batch: list[dict] = []

    for feed in feeds:
        try:
            articles = select(feed, state, limit=limit)
        except ingest.FeedParseError as exc:
            report["feeds"]["failed"] += 1
            report["feeds"]["failures"].append({"feed": feed["name"], "reason": str(exc)})
            continue

        report["feeds"]["succeeded"] += 1

        for article in articles:
            try:
                extraction = extract(article)
                summary_result = summarize(article, extraction["body"], feed_name=feed["name"])
            except (extract_module.ArticleExtractionError, summarize_module.SummarizeError) as exc:
                report["articles"]["failed"] += 1
                report["articles"]["failures"].append(
                    {"feed": feed["name"], "article_id": article["id"], "reason": str(exc)}
                )
                continue

            published = wiki.normalize_date(summary_result.get("published"), fallback=collected_date)
            filename = wiki.article_filename(
                summary_result.get("title"), published, existing=existing_filenames
            )
            existing_filenames.add(filename)

            meta = {
                "filename": filename,
                "title": summary_result.get("title") or "(제목 없음)",
                "published": published,
                "collected_date": collected_date,
                "feed_name": feed["name"],
            }
            new_state["processed"][article["id"]] = {
                "processed_at": now,
                "status": "ok",
                "meta": meta,
            }
            batch.append(
                {
                    "summary_result": summary_result,
                    "collected_date": collected_date,
                    "filename": filename,
                }
            )
            report["articles"]["succeeded"] += 1

    return {"batch": batch, "state": new_state, "report": report}


async def run_fetch_async(
    feeds: list[dict],
    state: dict,
    *,
    limit: int,
    now: str,
    collected_date: str,
    concurrency: int,
    select=ingest.select_new_articles,
    extract=extract_module.extract_body,
    summarize=summarize_module.summarize_article_async,
    on_progress=None,
) -> dict:
    """`run_fetch`의 순수 async 병렬판. 반환 계약(batch/state/report)은 동일하다.

    피드별 새 글 선정(`select`)은 순차로 수행해 피드 파싱 실패(`FeedParseError`)
    격리를 동기판과 동일하게 유지한다. 선정된 전체 글의 본문 확보+요약은
    `asyncio.Semaphore(concurrency)`로 동시 실행 개수를 제한해 병렬 수행한다.
    동기 `extract`는 이벤트 루프를 막지 않도록 `asyncio.to_thread`로 감싼다.

    병렬 처리가 모두 끝난 뒤, 파일명 배정·state 적재·리포트 집계는 입력 순서
    (피드 순서 × 각 피드 내 글 순서)대로 직렬 수행해 결정성을 보장한다
    (같은 날짜·슬러그 글이 여럿이어도 파일명 접미사·리포트 건수가 실행마다
    달라지지 않는다).

    `on_progress`(선택, 기본 `None`)는 `web/progress.py`가 정의한 이벤트 계약
    (`{"kind": "feed_started"|"article_done"|"article_failed", "feed": str}`)을
    받는 async 콜러블이다. 피드 선정 성공 시 `feed_started`를, 글 처리 완료 시점에
    `article_done`/`article_failed`를 즉시 방출해 실시간 진행 표시(폴링)에 쓰인다.
    `None`이면(CLI 경로, T18) 아무 것도 호출하지 않아 기존 회귀와 동일하게 동작한다.
    """
    new_state = {**state, "processed": dict(state.get("processed", {}))}
    existing_filenames = _existing_filenames(state)

    report = {
        "feeds": {"succeeded": 0, "failed": 0, "failures": []},
        "articles": {"succeeded": 0, "failed": 0, "failures": []},
    }
    batch: list[dict] = []

    feed_articles: list[tuple[dict, dict]] = []
    for feed in feeds:
        try:
            articles = select(feed, state, limit=limit)
        except ingest.FeedParseError as exc:
            report["feeds"]["failed"] += 1
            report["feeds"]["failures"].append({"feed": feed["name"], "reason": str(exc)})
            continue

        report["feeds"]["succeeded"] += 1
        if on_progress is not None:
            await on_progress({"kind": "feed_started", "feed": feed["name"]})
        feed_articles.extend((feed, article) for article in articles)

    semaphore = asyncio.Semaphore(concurrency)

    async def _process(feed: dict, article: dict) -> dict:
        async with semaphore:
            try:
                extraction = await asyncio.to_thread(extract, article)
                summary_result = await summarize(article, extraction["body"], feed_name=feed["name"])
            except (extract_module.ArticleExtractionError, summarize_module.SummarizeError) as exc:
                if on_progress is not None:
                    await on_progress({"kind": "article_failed", "feed": feed["name"]})
                return {"ok": False, "reason": str(exc)}
            if on_progress is not None:
                await on_progress({"kind": "article_done", "feed": feed["name"]})
            return {"ok": True, "summary_result": summary_result}

    results = await asyncio.gather(
        *(_process(feed, article) for feed, article in feed_articles)
    )

    for (feed, article), outcome in zip(feed_articles, results):
        if not outcome["ok"]:
            report["articles"]["failed"] += 1
            report["articles"]["failures"].append(
                {"feed": feed["name"], "article_id": article["id"], "reason": outcome["reason"]}
            )
            continue

        summary_result = outcome["summary_result"]
        published = wiki.normalize_date(summary_result.get("published"), fallback=collected_date)
        filename = wiki.article_filename(
            summary_result.get("title"), published, existing=existing_filenames
        )
        existing_filenames.add(filename)

        meta = {
            "filename": filename,
            "title": summary_result.get("title") or "(제목 없음)",
            "published": published,
            "collected_date": collected_date,
            "feed_name": feed["name"],
        }
        new_state["processed"][article["id"]] = {
            "processed_at": now,
            "status": "ok",
            "meta": meta,
        }
        batch.append(
            {
                "summary_result": summary_result,
                "collected_date": collected_date,
                "filename": filename,
            }
        )
        report["articles"]["succeeded"] += 1

    return {"batch": batch, "state": new_state, "report": report}
