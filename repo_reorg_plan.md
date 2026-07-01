# REXA 프로젝트 구조 정리 플랜

## 목적

- Git에 올리기 전에 루트 디렉토리에 흩어진 핵심 모듈을 패키지 내부로 정리한다.
- 진입점 `kakao_callback.py`는 유지하되, 실제 로직은 패키지 내부로 모은다.
- import 경로를 일관되게 만들어 `rexa` 패키지가 프로젝트의 중심이 되게 한다.

## 현재 구조에서 보이는 문제

- 루트에 중요한 런타임 모듈이 직접 놓여 있다.
  - `logger.py`
  - `chat_logging.py`
  - `llm_failover.py`
  - `memory.py`
- `memory.py`는 루트와 `rexa/memory.py`에 중복으로 존재한다.
- `pyproject.toml`의 `py-modules`에 루트 모듈들이 등록되어 있어서 패키지 구조가 섞여 있다.
- `models/`, `tools/`, `prompts/`는 패키지처럼 보이지만 루트 유틸 모듈에 직접 의존한다.
- `kakao_callback.py`가 엔트리포인트이면서 로깅 설정도 자체적으로 들고 있어서, 서버 진입점과 공통 런타임 코드가 분리되지 않았다.

## 현재 기준 진입점/핵심 흐름

1. `kakao_callback.py`
2. `from rexa import run`
3. `rexa/api.py`
4. `models/*`
5. `tools/*`

즉, `kakao_callback.py`는 바깥 인터페이스이고, 실제 애플리케이션 중심은 이미 `rexa/` 안에 있다. 정리 방향도 여기에 맞추는 게 안전하다.

## 정리 원칙

- 루트에는 배포/실행 진입점과 프로젝트 설정만 남긴다.
- 공통 런타임 코드는 모두 `rexa/` 아래로 이동한다.
- 한 번에 다 옮기지 말고, 먼저 내부 import를 바꾸고 마지막에 루트 파일을 비운다.
- 기존 실행 호환성을 위해 초기에는 루트 파일을 thin wrapper로 남길 수 있다.

## 구조 원칙

- `models`, `prompts`, `tools`는 최종적으로 `rexa/` 아래에 둔다.
- `tests`는 패키지 내부가 아니라 루트에 둔다.
- 문서 안에서 "1차 이행 구조"와 "최종 목표 구조"를 구분한다.

## 1차 이행 구조

```text
.
├── kakao_callback.py
├── main.py
├── pyproject.toml
├── requirements.txt
├── pytest.ini
├── rexa/
│   ├── __init__.py
│   ├── __main__.py
│   ├── api.py
│   ├── memory.py
│   ├── entrypoints/
│   │   └── kakao_callback.py
│   └── infra/
│       ├── logger.py
│       ├── chat_logging.py
│       └── llm_failover.py
├── models/
├── prompts/
├── tools/
└── tests/
```

## 파일별 정리 방향

- `kakao_callback.py`
  - 최종적으로는 `rexa/entrypoints/kakao_callback.py`로 핵심 로직 이동
  - 루트 `kakao_callback.py`는 배포 호환용 thin wrapper로 유지 가능
- `logger.py`
  - `rexa/infra/logger.py`로 이동
- `chat_logging.py`
  - `rexa/infra/chat_logging.py`로 이동
- `llm_failover.py`
  - `rexa/infra/llm_failover.py` 또는 `rexa/llm/failover.py`로 이동
  - 현재 의존성 범위를 보면 우선 `rexa/infra/llm_failover.py`가 변경 폭이 작다
- `memory.py`
  - 루트 파일 삭제 대상
  - `rexa/memory.py`만 단일 소스로 유지
- `models/`, `prompts/`, `tools/`
  - 최종적으로는 `rexa/models`, `rexa/prompts`, `rexa/tools`로 이동
  - 다만 import 변경 폭이 커서 1차와 2차를 나눠서 진행

## 단계별 실행 플랜

### 1단계: 중복 제거와 import 기준 확정

- `memory.py` 루트 파일과 `rexa/memory.py`가 사실상 같은지 확인
- 루트 `memory.py` 사용처가 없으면 삭제 대상으로 확정
- 공통 모듈 import 기준을 `rexa.*`로 통일

예시:

- `from logger import setup_logger`
  -> `from rexa.infra.logger import setup_logger`
- `from chat_logging import extract_token_usage`
  -> `from rexa.infra.chat_logging import extract_token_usage`
- `from llm_failover import run_with_failover`
  -> `from rexa.infra.llm_failover import run_with_failover`

### 2단계: 공통 런타임 모듈 이동

- 새 디렉토리 `rexa/infra/` 생성
- 아래 파일 이동
  - `logger.py`
  - `chat_logging.py`
  - `llm_failover.py`
- 내부 import를 전부 새 경로로 수정
- 필요하면 루트 파일은 아래 형태의 호환 wrapper로 잠시 유지

```python
from rexa.infra.logger import *
```

이 wrapper는 배포 안정화 후 제거한다.

### 3단계: Kakao 진입점 슬림화

- `kakao_callback.py`의 Flask/Kakao 인터페이스는 유지
- 내부 유틸, 응답 빌더, 공통 로깅은 `rexa/entrypoints/kakao_callback.py`로 분리
- 루트 `kakao_callback.py`는 아래 역할만 남긴다
  - app import
  - local run
  - 배포 서버 entrypoint

이 단계의 목적은 "루트에 파일이 있는 것" 자체보다 "루트 파일이 너무 많은 책임을 갖는 것"을 줄이는 데 있다.

### 4단계: 패키징 설정 정리

- `pyproject.toml`의 `py-modules` 제거 또는 최소화
- 가능하면 패키지 기반만 사용
- 예시
  - 유지: `packages = ["rexa", "models", "tools", "prompts"]`
  - 정리 후 목표: 공통 모듈도 전부 `rexa` 패키지 안으로 편입

루트 모듈이 사라지면 `py-modules = ["logger", "main", "llm_failover", "chat_logging"]`는 정리 대상이다.

### 5단계: 패키지 내부 편입

- `models/`, `tools/`, `prompts/`를 `rexa/` 아래로 이동
- import를 전부 `rexa.models`, `rexa.prompts`, `rexa.tools` 기준으로 변경
- 이 단계가 끝나야 최종 구조가 일관된다

권장 우선순위:

1. `infra` 정리
2. `memory` 중복 제거
3. `kakao_callback.py` 슬림화
4. `models/tools/prompts`를 `rexa/` 아래로 편입

## 추천 최종 트리

아래는 이 프로젝트의 최종 목표 구조다.

```text
.
├── kakao_callback.py                  # thin entrypoint
├── main.py                            # local/manual runner
├── pyproject.toml
├── requirements.txt
├── pytest.ini
├── rexa/
│   ├── __init__.py
│   ├── __main__.py
│   ├── api.py                         # run, run_query
│   ├── memory.py                      # Redis conversation memory
│   ├── entrypoints/
│   │   ├── __init__.py
│   │   └── kakao_callback.py          # callback handlers, response builders
│   └── infra/
│       ├── __init__.py
│       ├── logger.py                  # setup_logger, log helpers
│       ├── chat_logging.py            # token/log persistence
│       └── llm_failover.py            # provider failover, circuit breaker
│   ├── models/
│   ├── prompts/
│   └── tools/
└── tests/
```

## 이 구조를 추천하는 이유

- 현재 앱 중심이 이미 `rexa/api.py`에 있어서 큰 방향 전환이 아니다.
- 1차 정리와 최종 목표를 분리해서 볼 수 있다.
- 가장 지저분해 보이는 루트 핵심 모듈만 먼저 수습할 수 있다.
- `kakao_callback.py`를 완전히 없애지 않아 배포 진입점 호환성을 유지하기 쉽다.
- 최종적으로는 애플리케이션 구현이 `rexa/` 아래에 모여 패키지 경계가 선명해진다.

## 실제 작업 순서 제안

1. `rexa/infra/` 생성
2. `chat_logging.py` 이동
3. `logger.py` 이동
4. `llm_failover.py` 이동
5. 전역 import 수정
6. 테스트/수동 실행 확인
7. 루트 `memory.py` 삭제
8. `kakao_callback.py` 내부 보조 로직 분리
9. `models/`, `prompts/`, `tools/`를 `rexa/` 아래로 이동
10. 마지막에 `pyproject.toml` 정리

## 주의할 점

- `models/*`, `tools/*`, `prompts/*`, `rexa/api.py`에서 루트 import를 많이 쓰고 있어서 한 번에 이동하면 import 에러가 연쇄로 날 수 있다.
- 따라서 "파일 이동"보다 "import 경로 전환 + wrapper 유지"를 먼저 하는 편이 안전하다.
- `kakao_callback.py`는 외부에서 직접 실행될 가능성이 높으므로, 제일 마지막에 얇게 만드는 것이 낫다.

## 이번 플랜의 범위 밖

- `tools/archive/` 정리
- QA 산출물 정리
- 배포 스크립트(`deploy_rexa.sh`, `deploy_rexa.bat`) 재구성
- `tests/`를 패키지 내부로 넣는 구조 변경

## 한 줄 결론

정리 방향은 "앱 구현은 최종적으로 `rexa/` 아래에 모으고, `tests/`만 루트에 남긴다"가 맞다. 다만 실행 안정성을 위해 1차 이행과 최종 목표를 나눠서 진행하는 것이 안전하다.
