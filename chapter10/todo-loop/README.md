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

## 책의 전체 흐름 한 번에 재현하기

다음 명령은 책에서 설명한 작업 발견, 배정, 검증 실패와 재시도, 사람 이관, 승인값 반영, 재등록, 최종 완료를 차례로 실행합니다.

```bash
uv run python loop.py simulate
```

`fixture` 작업자는 LLM을 호출하지 않습니다. 정해진 변경을 적용해 책의 상태 전이를 항상 같은 결과로 재현합니다. 기존 `workspace`나 `.loop`가 있으면 초기화하기 전에 계속할지 묻습니다. 자동 실행 환경에서는 `--yes`를 붙일 수 있습니다.

```bash
uv run python loop.py simulate --yes
```

## 독자가 직접 한 작업 처리하기

```bash
uv run python loop.py run --once --worker manual
```

화면에 나온 완료 조건에 맞춰 `workspace/app/calc.py`를 수정한 뒤 Enter를 누릅니다. 컨트롤러가 작업자와 별도로 인수 테스트를 실행해 완료 여부를 판정합니다.

## 모든 분기 재현하기

시험용 작업자는 Claude Code나 다른 모델을 호출하지 않습니다. 정해진 변경을 만들어 정상 완료, 검증 실패 뒤 재시도, 외부 승인 대기를 한 번에 확인하게 합니다.

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

실제 호출이 시작되면 `[llm] Claude Code 요청 시작`이 표시되고, 응답을 받으면 실행 시간과 추정 비용이 출력됩니다.

검증 결과가 `retry`라면 같은 명령을 한 번 더 실행합니다. 직전 검증 결과가 다음 Claude Code 요청에 전달됩니다.

## 컨트롤러 검사

```bash
uv run pytest -q tests
```

운영체제별 파일 잠금, 여러 파일의 변경 범위 검사, 컨테이너 격리, 실제 비용 원장은 첫 실습에서 제외했습니다. 여러 작업자나 신뢰할 수 없는 저장소에 적용할 때 추가해야 합니다.
