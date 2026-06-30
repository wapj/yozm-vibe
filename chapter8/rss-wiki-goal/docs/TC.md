# RSS Wiki — QA 테스트 케이스 (TC)

작성일: 2026-07-01  
범위: PRD MVP 기능 전체 (§3, §9)  
테스트 방식: FastAPI TestClient 기반 E2E (DB 실제 사용, 외부 서비스 mock)

---

## 화면/기능 매핑

| TC ID  | 경로 / 기능              | HTTP 메서드 |
|--------|--------------------------|-------------|
| TC-F01 | 피드 목록                | GET /feeds  |
| TC-F02 | 피드 추가 — 정상         | POST /feeds/add |
| TC-F03 | 피드 추가 — 빈 URL       | POST /feeds/add |
| TC-F04 | 피드 추가 — 중복         | POST /feeds/add |
| TC-F05 | 피드 활성/비활성 토글    | POST /feeds/{id}/toggle |
| TC-F06 | 피드 삭제 + CASCADE      | POST /feeds/{id}/delete |
| TC-C01 | 홈(카테고리 목록) — 빈 상태 | GET / |
| TC-C02 | 홈 — 카테고리 있을 때    | GET / |
| TC-C03 | 홈 — 미읽음 카테고리 상단 정렬 | GET / |
| TC-C04 | 카테고리 위키 상세       | GET /categories/{id} |
| TC-C05 | 카테고리 위키 — 존재하지 않는 ID | GET /categories/9999 |
| TC-C06 | 카테고리 위키 방문 → 읽음 처리 | GET /categories/{id} |
| TC-C07 | 카테고리 이름 수정       | POST /categories/{id}/rename |
| TC-C08 | 카테고리 이름 수정 — 빈 이름 | POST /categories/{id}/rename |
| TC-C09 | 카테고리 상위 지정       | POST /categories/{id}/parent |
| TC-C10 | 카테고리 상위 해제       | POST /categories/{id}/parent |
| TC-C11 | 카테고리 병합 — 글 이동  | POST /categories/{id}/merge |
| TC-C12 | 카테고리 병합 — 같은 ID  | POST /categories/{id}/merge |
| TC-C13 | 카테고리 관리 화면       | GET /categories/manage |
| TC-S01 | 검색 — 빈 쿼리           | GET /search |
| TC-S02 | 검색 — 결과 있음 (FTS5)  | GET /search?q=키워드 |
| TC-S03 | 검색 — 결과 없음         | GET /search?q=없는키워드 |
| TC-L01 | 로그 페이지 — 빈 상태    | GET /logs |
| TC-L02 | 로그 페이지 — 로그 있음  | GET /logs |
| TC-A01 | 수동 수집 트리거 — 피드 없음 | POST /api/fetch |
| TC-A02 | 수동 수집 트리거 — 피드 있음 (RSS mock) | POST /api/fetch |

---

## TC 상세

### TC-F01: 피드 목록 화면 정상 렌더링
- **전제조건**: 피드 없음
- **입력**: GET /feeds
- **기대 결과**: 200 OK, HTML 응답, "피드 관리" 텍스트 포함

### TC-F02: 피드 추가 — 정상
- **입력**: POST /feeds/add, url=https://example.com/feed
- **기대 결과**: 303 Redirect → /feeds, DB에 피드 레코드 생성, is_active=1

### TC-F03: 피드 추가 — 빈 URL
- **입력**: POST /feeds/add, url="" (빈 문자열)
- **기대 결과**: 400 Bad Request

### TC-F04: 피드 추가 — 중복 URL
- **전제조건**: 동일 URL 피드 이미 존재
- **입력**: POST /feeds/add, url=동일URL
- **기대 결과**: 409 Conflict

### TC-F05: 피드 활성/비활성 토글
- **전제조건**: is_active=1 피드 존재
- **입력**: POST /feeds/{id}/toggle
- **기대 결과**: 303 Redirect, DB에서 is_active=0으로 변경
- **2차 토글**: 다시 is_active=1로 복귀

### TC-F06: 피드 삭제 및 연관 글 CASCADE 삭제
- **전제조건**: 피드에 연결된 articles 존재
- **입력**: POST /feeds/{id}/delete
- **기대 결과**: 303 Redirect, 피드 삭제, 연관 articles도 삭제

### TC-C01: 홈 화면 — 빈 상태
- **전제조건**: 카테고리 없음
- **기대 결과**: 200 OK, "수집된 카테고리가 없습니다" 텍스트 포함

### TC-C02: 홈 화면 — 카테고리 있을 때
- **전제조건**: 카테고리 2개 (parent_id=NULL)
- **기대 결과**: 200 OK, 카테고리 이름이 목록에 표시

### TC-C03: 홈 — 미읽음 카테고리 상단 정렬
- **전제조건**: 카테고리 A(has_unread=0), 카테고리 B(has_unread=1)
- **기대 결과**: B가 A보다 먼저 HTML에 등장

### TC-C04: 카테고리 위키 상세 정상 조회
- **전제조건**: 카테고리, wiki_page, articles 존재
- **기대 결과**: 200 OK, 위키 내용, 원문 목록 표시

### TC-C05: 카테고리 — 존재하지 않는 ID
- **입력**: GET /categories/9999
- **기대 결과**: 404 Not Found

### TC-C06: 카테고리 방문 시 읽음 처리
- **전제조건**: has_unread_updates=1
- **동작**: GET /categories/{id} 호출
- **기대 결과**: DB에서 has_unread_updates=0으로 변경

### TC-C07: 카테고리 이름 수정
- **입력**: POST /categories/{id}/rename, name="새이름"
- **기대 결과**: 303 Redirect, DB에서 name="새이름", is_user_edited=1

### TC-C08: 카테고리 이름 수정 — 빈 이름
- **입력**: POST /categories/{id}/rename, name=""
- **기대 결과**: 400 Bad Request

### TC-C09: 카테고리 상위 지정
- **전제조건**: 부모 카테고리, 자식 카테고리 2개
- **입력**: POST /categories/{child_id}/parent, parent_id={parent_id}
- **기대 결과**: 303 Redirect, DB에서 parent_id 업데이트

### TC-C10: 카테고리 상위 해제
- **전제조건**: parent_id가 설정된 카테고리
- **입력**: POST /categories/{id}/parent, parent_id="" (빈값)
- **기대 결과**: parent_id=NULL로 변경

### TC-C11: 카테고리 병합 — 글 이동 및 소스 삭제
- **전제조건**: 소스 카테고리(글 2개), 타겟 카테고리
- **입력**: POST /categories/{src_id}/merge, target_id={tgt_id}
- **기대 결과**: 303 Redirect, 소스 글이 타겟으로 이동, 소스 merged_into_id 설정

### TC-C12: 카테고리 병합 — 자기 자신 지정
- **입력**: POST /categories/{id}/merge, target_id={동일id}
- **기대 결과**: 400 Bad Request

### TC-C13: 카테고리 관리 화면
- **기대 결과**: 200 OK, HTML 테이블 포함

### TC-S01: 검색 — 빈 쿼리
- **입력**: GET /search (q 없음)
- **기대 결과**: 200 OK, 검색 폼 표시, 결과 없음

### TC-S02: 검색 — FTS5 키워드 매칭
- **전제조건**: articles에 title="AI 기술 동향" 데이터 존재
- **입력**: GET /search?q=AI
- **기대 결과**: 200 OK, "AI 기술 동향" 결과 포함

### TC-S03: 검색 — 결과 없음
- **입력**: GET /search?q=절대없는키워드xyz
- **기대 결과**: 200 OK, 결과 없음 표시

### TC-L01: 로그 페이지 — 빈 상태
- **기대 결과**: 200 OK, 빈 테이블

### TC-L02: 로그 페이지 — 로그 있음
- **전제조건**: job_logs에 레코드 2건
- **기대 결과**: 200 OK, 로그 항목 표시

### TC-A01: 수동 수집 트리거 — 활성 피드 없음
- **입력**: POST /api/fetch
- **기대 결과**: 200 OK, {"started": true, "feeds": 0}

### TC-A02: 수동 수집 트리거 — RSS 수집 시뮬레이션
- **전제조건**: 활성 피드 존재, feedparser·LLM·extractor mock
- **동작**: 신규 글 1건 처리
- **기대 결과**: articles에 레코드 생성, categories 생성, wiki_pages 생성
