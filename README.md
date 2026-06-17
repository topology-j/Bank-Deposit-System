# 팀프로젝트 — 은행 수신 시스템 + 목표 달성 에이전트

ERD 기반 수신 업무 시스템과 Tool Calling 기반 금융 목표 달성 에이전트를 구현한 풀스택 프로젝트입니다.  
FastAPI 백엔드(`implemented_files/`)와 MSA 구조 인터넷뱅킹 플랫폼(`internet_banking/`)으로 구성됩니다.

---

## 목차

1. [프로젝트 구성](#1-프로젝트-구성)
2. [주요 구현 기능](#2-주요-구현-기능)
3. [목표 달성 에이전트 (Goal Agent)](#3-목표-달성-에이전트-goal-agent)
4. [consultation-service — 챗봇 연동](#4-consultation-service--챗봇-연동)
5. [실행 방법](#5-실행-방법)
6. [환경 변수](#6-환경-변수)
7. [API 명세](#7-api-명세)
8. [파일 구조](#8-파일-구조)
9. [테스트](#9-테스트)

---

## 1. 프로젝트 구성

| 디렉터리 | 역할 | 포트 |
|---|---|---|
| `implemented_files/backend/` | FastAPI 수신 관리 API + Goal Agent | 8000 |
| `internet_banking/` | MSA 인터넷뱅킹 (Java Spring Boot + Python) | 8081~8090 |

### implemented_files/backend

ERD 18개 테이블 기반 FastAPI 서버입니다. SQLAlchemy ORM, Alembic 마이그레이션, Tool Calling Agent를 포함합니다.

- **수신 업무 CRUD**: 상품·계약·계좌·거래·금리·특약 18개 테이블 전체 CRUD API
- **거래 처리**: 입금·출금·이체·결제·적금납입·역거래(취소)
- **이자 지급**: 계약별 이자 지급 기록
- **Goal Agent**: 자연어 금융 목표 분석, Tool Calling 기반 적정 상품 추천

### internet_banking

MSA 구조 인터넷뱅킹 플랫폼으로 팀 전체가 공동 개발하는 영역입니다. 이 레포에서는 `consultation-service`의 저축 목표 플래너(SAVINGS_GOAL)와 Goal Agent 연동 부분을 담당합니다.

---

## 2. 주요 구현 기능

### 수신 상품 관리

- 예금·적금·청약·입출금 상품 등록·조회·수정
- 상품 상태 관리 (판매중·판매중지·만기)
- 가입 대상·방식·금리·기간 조건 관리
- 기간별·금액 구간별 금리 설정

### 계약·계좌·거래 관리

```
상품 등록 → 고객 계약 체결 → 계좌 자동 생성 → 거래 발생 → 금리 적용 → 특약 동의 관리
```

- 계약 생성 시 계좌 자동 생성
- 가입금액·기간 범위 검증
- 만기 처리·중도해지·계약 상태 전이
- 입금·출금·이체·적금납입·역거래 처리

### 금리·특약 관리

- 기본금리·우대금리 등록 및 계약별 적용 이력
- 수신 특약 등록·상품별 연결·고객 동의 관리

---

## 3. 목표 달성 에이전트 (Goal Agent)

`implemented_files/backend/app/agent_goal_chat.py`에 구현된 Tool Calling 기반 에이전트입니다.

### 왜 에이전트인가

기존 `/agent/goal/analyze`는 입력과 무관하게 항상 동일한 순서로 10개 함수를 실행하는 고정 워크플로우였습니다. Goal Agent는 다음을 개선합니다.

| 항목 | 기존 (`/analyze`) | 에이전트 (`/chat`) |
|---|---|---|
| 입력 방식 | 숫자 직접 전달 | 자연어 입력 |
| 실행 순서 | 항상 고정 | 상황에 맞게 동적 결정 |
| 정보 부족 시 | 0원으로 강행 분석 | 추가 질문 생성 후 중단 |
| 달성 불가 시 | 동일 결과 구조 반환 | 실패 원인·대안 3가지 추가 제공 |

### 아키텍처

```
사용자 (자연어)
    ↓
POST /agent/goal/chat
    ↓
run_goal_agent()
    ├── Claude API → tool_use 블록 수신
    ├── execute_tool() → Python 함수 실행 (DB 조회·계산)
    ├── 결과를 ctx(누산기)에 저장
    └── tool_result 전달 → 다음 턴 재진입 (최대 20회)
    ↓
_build_response(ctx) → JSON 반환
```

**Claude의 역할**: 자연어에서 goal_amount·goal_months 추출, 상황에 맞는 도구 선택 및 실행 순서 결정. **수치 계산 없음.**  
**Python의 역할**: 11개 도구 함수 실제 구현, DB 조회, Decimal 계산(ROUND_DOWN), ctx 관리.

### Mock 모드

`ANTHROPIC_API_KEY`가 없을 때 자동으로 Mock 모드로 전환됩니다. `run_goal_agent_mock()`이 `agent_goal_planner.analyze_goal()`을 직접 호출해 Claude API 없이 분석 결과를 반환합니다. consultation-service에서 호출 시 응답 메시지 앞에 `[Goal Agent Mock]` 레이블이 붙어 구분할 수 있습니다.

### 도구 목록 (11개)

| 도구 | 역할 |
|---|---|
| `ask_follow_up` | 정보 부족 시 추가 질문 생성 (즉시 루프 종료) |
| `get_customer_accounts` | 활성 계좌 목록·잔액 조회 |
| `get_recent_transactions` | 최근 3개월 거래 내역 조회 |
| `get_available_products` | 판매 중인 예금·적금 상품 조회 |
| `analyze_cash_flow` | 월 평균 수입·지출·잉여자금 계산 |
| `evaluate_goal_feasibility` | 달성 가능성 판단 (ACHIEVABLE / TIGHT / DIFFICULT / IMPOSSIBLE) |
| `generate_failure_reasons` | 실패 원인 분석 (ACHIEVABLE이 아닐 때) |
| `generate_alternatives` | 대안 3가지 생성 (기간 연장·저축 증가·상품 변경) |
| `generate_strategies` | 안정형·수익형·균형형 3전략 생성 |
| `build_monthly_plan` | 월별 납입 계획표 생성 |
| `build_recommendation_reason` | 추천 사유 4개 항목 구조화 |

### 달성 가능성 판정 기준

| 판정 | 조건 (잉여자금 / 필요 월 저축액 비율) |
|---|---|
| `ACHIEVABLE` | 비율 ≥ 1.2 |
| `TIGHT` | 비율 ≥ 0.9 |
| `DIFFICULT` | 비율 ≥ 0.6 |
| `IMPOSSIBLE` | 비율 < 0.6 또는 잉여자금 ≤ 0 |

### Agent Loop 실행 흐름

**Case A — 정보 부족**
```
"돈 모으고 싶어" → ask_follow_up 호출 → 즉시 종료
→ need_more_info: true, follow_up_question 반환
```

**Case B — 달성 가능 (ACHIEVABLE)**
```
"3년 안에 5000만원" → 계좌·거래·상품 조회 → 현금흐름 분석
→ ACHIEVABLE 판정 → 3전략 생성 → 월별 계획 → 추천 사유
(총 8개 도구, failure_reasons·alternatives 미호출)
```

**Case C — 달성 불가 (IMPOSSIBLE)**
```
"6개월 안에 1억원" → 계좌·거래·상품 조회 → 현금흐름 분석
→ IMPOSSIBLE 판정 → 실패 원인 3건 → 대안 3가지 → 3전략 → 월별 계획
(총 10개 도구)
```

---

## 4. consultation-service — 챗봇 연동

`internet_banking/services/consultation-service/`에 구현된 Python FastAPI 서비스가 Goal Agent를 챗봇에 연동합니다.

### SAVINGS_GOAL 라우팅 흐름

```
챗봇 메시지 수신
    ↓
services.py handle_message()
    ├── _SESSION[cid] 세션 존재? → 무조건 SAVINGS_GOAL로 강제 라우팅
    ├── 없으면 키워드 분류 (_is_savings_goal)
    └── 없으면 LLM 분류기
    ↓
GOAL_AGENT_ENABLED=true AND 세션 없음 → Goal Agent HTTP 호출 (포트 8000)
GOAL_AGENT_ENABLED=false OR 세션 있음 → savings_goal.py 직접 실행
```

**세션 우선 원칙**: `_SESSION[cid]`에 SAVINGS_GOAL 세션이 있으면 어떤 Intent 분류 결과보다 우선 처리합니다. "백만원"처럼 맥락 없이는 저축 관련어로 분류되지 않는 입력도 세션이 있으면 올바르게 월 납입액으로 처리됩니다.

### SAVINGS_GOAL 세션 상태

| 상태 | 진입 조건 | 다음 단계 |
|---|---|---|
| `ASKING_GOAL` | "돈 모으고 싶어" 등 첫 진입, 정보 불완전 | 목표 금액·기간 질문 |
| `ASKED_MONTHLY` | 목표 금액·기간 파악 완료 | 월 납입 가능 금액 질문 |
| `RESULT_SHOWN` | 월 납입액 입력 완료 | 상품 추천 카드 표시 |

### 한국어 금액·기간 파싱

`savings_goal.py`의 `_normalize_korean_amount`, `_parse_months` 함수가 다음을 처리합니다.

| 입력 예시 | 파싱 결과 |
|---|---|
| `일년에 천만원` | 목표 10,000,000원, 기간 12개월 |
| `이년 이천만원` | 목표 20,000,000원, 기간 24개월 |
| `육개월 오백만원` | 목표 5,000,000원, 기간 6개월 |
| `백만원` (ASKED_MONTHLY 상태) | 월 납입 1,000,000원 |
| `매달 백오십만원` | 월 납입 1,500,000원 |

### 환경 변수 (consultation-service)

| 변수 | 기본값 | 설명 |
|---|---|---|
| `GOAL_AGENT_ENABLED` | `true` | Goal Agent 연동 여부 |
| `GOAL_AGENT_URL` | `http://host.docker.internal:8000` | Goal Agent 엔드포인트 |

---

## 5. 실행 방법

### 사전 조건

- Python 3.11+
- PostgreSQL 16 (또는 Docker Desktop)
- Node.js 20+ (프론트엔드 선택)

### FastAPI 백엔드 (implemented_files)

```powershell
# DB 실행
docker compose up -d

# 백엔드 실행
cd implemented_files/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy ..\.env.example .env   # .env 파일 생성 후 DB URL 설정
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

접속:
- API 문서: http://127.0.0.1:8000/docs
- 주요 엔드포인트: http://127.0.0.1:8000/agent/goal/chat

### 인터넷뱅킹 전체 실행 (internet_banking)

```powershell
cd internet_banking
docker compose up -d
```

consultation-service만 재시작 (코드 변경 후):

```powershell
docker restart ib-consultation-service
```

로그 확인:

```powershell
docker logs ib-consultation-service --tail=50
# [savings_goal.routing] 접두어 로그로 세션 상태 확인 가능
```

---

## 6. 환경 변수

`.env.example` 파일을 복사해 `.env`를 만든 후 값을 채웁니다.

```env
# DB
DATABASE_URL=postgresql://user:password@localhost:5432/bankdb

# Goal Agent (Claude API)
ANTHROPIC_API_KEY=         # 비워두면 자동으로 Mock 모드 전환

# consultation-service
GOAL_AGENT_ENABLED=true
GOAL_AGENT_URL=http://host.docker.internal:8000
```

`ANTHROPIC_API_KEY`가 없어도 서버는 정상 기동됩니다. Goal Agent 호출 시 Mock 모드로 자동 fallback됩니다.

---

## 7. API 명세

### POST /agent/goal/chat

자연어 금융 목표를 입력받아 Tool Calling Agent가 분석 후 결과를 반환합니다.

**Request**

```json
{
  "customer_id": "CUST001",
  "message": "3년 안에 5000만원 모으고 싶어"
}
```

**Response (달성 가능)**

```json
{
  "agent_type": "GOAL_BASED_FINANCIAL_AGENT",
  "need_more_info": false,
  "follow_up_question": null,
  "feasibility": {
    "feasibility": "ACHIEVABLE",
    "goal_amount": 50000000.0,
    "goal_months": 36,
    "monthly_surplus": 2000000.0,
    "required_monthly_saving": 1250000.0,
    "surplus_to_required_ratio": 1.6,
    "is_feasible": true
  },
  "failure_reasons": [],
  "alternatives": [],
  "strategies": [
    {"name": "안정형", "strategy_type": "STABLE", "achievement_rate": 72.5},
    {"name": "수익형", "strategy_type": "GROWTH", "achievement_rate": 141.7},
    {"name": "균형형", "strategy_type": "BALANCED", "achievement_rate": 103.3}
  ],
  "monthly_plan": [...],
  "agent_steps": [...],
  "warning": null
}
```

**Response (정보 부족)**

```json
{
  "agent_type": "GOAL_BASED_FINANCIAL_AGENT",
  "need_more_info": true,
  "follow_up_question": "목표 금액과 목표 기간을 알려주세요. 예: '3년 안에 5000만원'"
}
```

**Response (달성 불가)**

```json
{
  "need_more_info": false,
  "feasibility": {"feasibility": "IMPOSSIBLE", ...},
  "failure_reasons": [
    "월 저축 가능 금액 부족: 목표 달성에 월 15,833,333원이 필요하지만 ...",
    "목표 기간 부족: ...",
    "초기 자산 부족: ..."
  ],
  "alternatives": [
    {"type": "EXTEND_PERIOD", "suggested_goal_months": 54, "reason": "..."},
    {"type": "INCREASE_MONTHLY_SAVING", "additional_amount": 13650000.0, "reason": "..."},
    {"type": "CHANGE_PRODUCT_MIX", "achievement_rate": 14.8, "reason": "..."}
  ]
}
```

**에러 응답**

| HTTP | 조건 | 메시지 |
|---|---|---|
| 400 | customer_id 또는 message 누락 | `"customer_id and message are required"` |
| 404 | 해당 고객 활성 계좌 없음 | `"no active accounts found for customer"` |
| 500 | API 키 미설정·DB 오류 | 상세 오류 메시지 |

### 수신 업무 CRUD API

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET/POST` | `/api/{table_name}` | 18개 테이블 CRUD |
| `POST` | `/contracts` | 계약 생성 + 계좌 자동 생성 |
| `POST` | `/transactions/deposit` | 입금 |
| `POST` | `/transactions/withdraw` | 출금 |
| `POST` | `/transactions/transfer` | 이체 |
| `POST` | `/transactions/savings-payment` | 적금 납입 |
| `POST` | `/transactions/{id}/reversal` | 역거래 (취소) |
| `POST` | `/interests/pay` | 이자 지급 기록 |
| `POST` | `/agent/goal/analyze` | 고정 워크플로우 목표 분석 (기존) |
| `POST` | `/agent/goal/chat` | Tool Calling Agent 목표 분석 (신규) |

---

## 8. 파일 구조

```
teamproject/
├── implemented_files/
│   └── backend/
│       ├── app/
│       │   ├── main.py               # FastAPI 앱, 라우터 (POST /agent/goal/chat 포함)
│       │   ├── config.py             # Settings (anthropic_api_key 포함)
│       │   ├── models.py             # SQLAlchemy 모델 (18개 테이블)
│       │   ├── services.py           # 거래·이자·계약 서비스 로직
│       │   ├── registry.py           # 라우터 등록
│       │   ├── agent_goal_chat.py    # Tool Calling Agent (run_goal_agent, Mock 모드)
│       │   ├── agent_goal_planner.py # 수치 계산 엔진 (단리·Decimal)
│       │   ├── agent_maturity.py     # 만기 처리 에이전트
│       │   └── utils.py              # 공통 유틸
│       ├── init_db.py                # DB 초기화 스크립트
│       ├── verify_all.py             # 전체 검증 스크립트
│       ├── start_server.bat          # Windows 서버 시작 스크립트
│       └── GOAL_AGENT_DOCS.md        # Goal Agent 상세 문서 (API·다이어그램·면접 Q&A)
│
├── internet_banking/                 # MSA 인터넷뱅킹 (서브모듈)
│   ├── docker-compose.yml            # GOAL_AGENT_ENABLED, GOAL_AGENT_URL 환경변수 추가
│   └── services/
│       └── consultation-service/
│           └── app/
│               ├── services.py       # 세션 우선 SAVINGS_GOAL 라우팅
│               └── features/
│                   └── savings_goal.py  # 한국어 파싱, 멀티턴 세션 관리
│
├── .env.example                      # 환경 변수 예시
├── .gitignore
└── README.md
```

### 핵심 설계 원칙

**Claude vs Python 역할 분리**  
Claude는 "무엇을 할지"만 결정합니다. DB 조회·이자 계산·대안 시뮬레이션은 모두 Python이 담당합니다. Context 누산기(`ctx`)에 결과를 축적하며 Claude에게는 집계 요약만 전달해 민감 데이터 노출과 할루시네이션을 방지합니다.

**세션 우선 라우팅**  
consultation-service에서 SAVINGS_GOAL 세션이 존재하면 LLM 분류기보다 세션 처리가 우선합니다. "백만원"처럼 단독으로는 저축 관련어로 분류되지 않는 입력도 세션 context에서 올바르게 처리됩니다.

**Mock 모드 fallback**  
`ANTHROPIC_API_KEY`가 없어도 서버가 죽지 않습니다. Mock 모드에서는 Python 계산 엔진을 직접 호출해 동일한 분석 결과를 반환합니다.

---

## 9. 테스트

### Goal Agent 단위 테스트

```powershell
cd implemented_files/backend
python -m pytest tests/ -q
```

Mock 테스트로 Claude API 호출 없이 3가지 케이스를 검증합니다.

| 케이스 | 입력 | 도구 수 | 검증 항목 |
|---|---|---|---|
| Case A | "돈 모으고 싶어" | 1 (ask_follow_up) | need_more_info=true |
| Case B | "3년 안에 5000만원" | 8 | ACHIEVABLE, 월별 계획 36개월 |
| Case C | "6개월 안에 1억원" | 10 | IMPOSSIBLE, failure_reasons 3건, alternatives 3개 |

### consultation-service 테스트

```powershell
cd internet_banking/services/consultation-service
python -m pytest tests/ -q
```

### 로그 모니터링

SAVINGS_GOAL 라우팅 상태는 컨테이너 로그에서 `[savings_goal.routing]` 접두어로 확인합니다.

```
[savings_goal.routing] incoming_message='일년에 천만원' current_session_stage=ASKING_GOAL forced_savings_goal_route=True
[savings_goal.routing] incoming_message='백만원' current_session_stage=ASKED_MONTHLY forced_savings_goal_route=True
[savings_goal.routing] _handle_payment_answer query='백만원' parsed_monthly_payment=1000000 is_lump=False
```

---

## 주의 사항

- `main` 브랜치 직접 커밋·푸시 금지
- `.env` 파일 커밋 금지 (`.gitignore`에 포함)
- `ANTHROPIC_API_KEY`는 코드에 하드코딩 금지
- internet_banking 서브모듈 변경 시 서브모듈 내 먼저 커밋 후 루트 커밋
