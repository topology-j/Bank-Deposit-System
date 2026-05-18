# TeamProject ERD Fullstack

ERD 기준 18개 테이블을 PostgreSQL + FastAPI + Vue/Vite로 구현한 실행 프로젝트입니다.

## 구성

- `backend/`: FastAPI API 서버, SQLAlchemy ORM, Alembic migration
- `frontend/`: Vue + Vite 관리 화면
- `docker-compose.yml`: PostgreSQL 개발 DB
- `.env.example`: 환경 변수 예시

## 실행

```powershell
docker compose up -d

cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy ..\.env.example .env
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

다른 터미널:

```powershell
cd frontend
npm install
npm run dev
```

## 접속

- API 문서: http://127.0.0.1:8000/docs
- 프론트: http://127.0.0.1:5173

## 구현 범위

- ERD 18개 테이블 CRUD API: `/api/{table_name}`
- 계약 생성 + 계좌 자동 생성: `POST /contracts`
- 거래 처리:
  - `POST /transactions/deposit`
  - `POST /transactions/withdraw`
  - `POST /transactions/transfer`
  - `POST /transactions/payment`
  - `POST /transactions/savings-payment`
  - `POST /transactions/{transaction_id}/reversal`
- 이자 지급 기록: `POST /interests/pay`

## 거래 추가 컬럼

- `depositor_customer_id`
- `depositor_name`
- `delegate_customer_id`
- `delegate_customer_name`
