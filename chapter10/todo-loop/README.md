# TODO 처리 루프

10장 루프 엔지니어링 실습용 주문 계산기입니다. 독자는 작업 계약과 인수 테스트, 상태 저장, 작업 배정, 검증, 재시도, 사람 이관을 차례로 작성합니다.

## 준비

macOS와 Linux에서는 Bash 또는 zsh, Windows에서는 Git Bash를 사용합니다.

```bash
cd chapter10/todo-loop
uv sync
uv run python loop.py reset
uv run python loop.py status
```

## 독자가 직접 한 작업 처리하기

```bash
uv run python loop.py run --once --worker manual
```

화면에 나온 완료 조건에 맞춰 `workspace/app/calc.py`를 수정한 뒤 Enter를 누릅니다. 컨트롤러가 작업자와 별도로 인수 테스트를 실행해 완료 여부를 판정합니다.

## 모든 분기 재현하기

시험용 작업자는 같은 변경을 만들어 정상 완료, 검증 실패 뒤 재시도, 외부 승인 대기를 한 번에 확인하게 합니다.

```bash
uv run python loop.py reset
uv run python loop.py run --worker fixture
uv run python loop.py status
```

환율 작업이 `needs_human`에 남으므로 첫 실행은 종료 코드 2를 반환합니다. 실행 오류가 아니라 자동으로 처리할 일은 끝났지만 사람이 확인할 일이 남았다는 뜻입니다.

```bash
export EXPECTED_USD_RATE=1325.5
uv run python loop.py requeue CALC-003 \
  --reason "운영팀이 USD 기준 환율 1325.5를 승인함"
uv run python loop.py run --worker fixture
uv run python -m pytest -q checks
```

## Claude Code 연결하기

먼저 Claude Code에 로그인되어 있어야 합니다.

```bash
uv run python loop.py reset
uv run python loop.py run --once --worker claude
```

컨트롤러는 작업마다 새 Claude Code 프로세스를 시작합니다. 도구는 `workspace/app/calc.py`를 읽고 편집하는 데만 사용하며, 테스트와 완료 판정은 컨트롤러가 별도로 수행합니다.

## 컨트롤러 검사

```bash
uv run pytest -q tests
```

운영체제별 파일 잠금, 여러 파일의 변경 범위 검사, 컨테이너 격리, 실제 비용 원장은 첫 실습에서 제외했습니다. 여러 작업자나 신뢰할 수 없는 저장소에 적용할 때 추가해야 합니다.
