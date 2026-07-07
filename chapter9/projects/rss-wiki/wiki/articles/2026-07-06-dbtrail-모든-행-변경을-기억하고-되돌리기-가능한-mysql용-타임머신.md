# dbtrail - 모든 행 변경을 기억하고 되돌리기 가능한 MySQL용 타임머신

- 원문: [https://news.hada.io/topic?id=31159](https://news.hada.io/topic?id=31159)
- 발행일: 2026-07-06
- 피드: GeekNews - 개발/기술/스타트업 뉴스 서비스

## 요약

dbtrail은 MySQL의 바이너리 로그를 실시간으로 수신하여 모든 행 변경 이력을 before/after 이미지와 함께 검색 가능한 형태로 보관하는 오픈소스 도구입니다. 락이나 스키마 변경 없이 특정 시점으로의 복구(point-in-time recovery)를 지원하며, 손상된 행만 선별해 역방향 SQL을 생성하는 정밀 Undo와 cascade delete로 삭제된 자식 행 복원까지 가능합니다. 변경의 주체(사용자·호스트·클라이언트)를 식별하는 감사 기능, 웹 콘솔, `reconstruct` CLI, MCP 서버를 제공하여 Claude 등 AI 클라이언트에서도 이력 검색과 복구안 작성이 가능합니다. MySQL 8.0 이상과 ROW 포맷 binlog가 필요하며, Apache 2.0 라이선스로 상업용을 포함해 자유롭게 사용할 수 있습니다.

## 핵심 포인트

- **동작 방식**: 복제 프로토콜로 binlog를 tail하여 모든 행 변경을 완전한 before/after 이미지로 인덱싱. 디스크상의 binlog 파일 접근이 불필요
- **복구 기능**: 락·스키마 변경·복원 대기 없는 point-in-time recovery, 손상된 행만 골라내는 정밀 역방향 SQL 생성
- **Cascade 복구**: `ON DELETE CASCADE`로 삭제된 자식 행 재구성, `ON DELETE SET NULL`로 지워진 FK 복원. InnoDB가 binlog 하위 단계에서 처리해 다른 도구가 감지하지 못하는 변경까지 포함
- **Time-travel 조회**: 웹 콘솔 또는 `reconstruct` CLI로 임의 시점의 행·테이블 상태 조회 (라이브 SQL `AS OF` 인터페이스는 ProxySQL 추가 필요)
- **변경 주체 추적**: 어떤 DB 사용자·호스트·클라이언트 프로그램이 변경했는지 식별하며, audit plugin 유무에 따라 증명 가능 범위를 구분
- **검증 도구**: `bintrail verify`(복구 결과가 원본을 재현하는지 검사), `bintrail status`(캡처 스트림 누락 구간 표시), `bintrail doctor`(요구 설정 점검)
- **AI 연동**: MCP 서버를 통해 Claude 등 MCP 클라이언트가 변경 이력 검색과 복구안 초안 작성 가능
- **지원 환경**: MySQL·Percona·RDS·Aurora·Cloud SQL, MySQL 8.0 이상 + `binlog_format=ROW` + `binlog_row_image=FULL` 필요
- **라이선스**: Apache 2.0 (상업용·프로덕션 포함 자유 사용)
