# STEADYCORP

A drop-site for the paint/art brand **STEADYCORP**, selling limited numbered art pieces called **STEADY BRICKS**.

**Concept:** a streetwear-style monthly "drop" — 20 numbered bricks (#1–#20), FCFS numbering, revealed only when you type the drop's secret name (learned from Instagram). You earn the right to buy a brick by winning a short brick-**stacker** game; winning atomically claims the lowest available brick and starts a hold-with-expiry, then Stripe checkout.

See [`STEADYCORP_PLAN.md`](./STEADYCORP_PLAN.md) for the full design and rationale.

## Stack

| Layer    | Tech |
|----------|------|
| Backend  | Python, FastAPI, SQLAlchemy, Alembic, Pydantic |
| Frontend | React, TypeScript, Vite, Tailwind |
| DB       | PostgreSQL (prod) / SQLite (dev), env-driven |
| Services | Stripe (test mode), Cloudflare R2 (images), Resend (email); Redis optional |

## The headline engineering problem

**Limited-inventory drop concurrency** — guarantee *exactly 20 sold* under many simultaneous winners, via an atomic claim (`SELECT ... FOR UPDATE SKIP LOCKED`) and a per-brick state machine `available → held → sold`.

## Local development

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in secrets
alembic upgrade head          # once migrations exist
uvicorn app.main:app --reload
```

API docs at http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

App at http://localhost:5173

## Layout

```
backend/app/
  main.py        FastAPI app + router wiring
  config.py      settings (pydantic-settings, env-driven)
  db.py          engine + session
  models/        SQLAlchemy models  (schema — WIP)
  schemas/       Pydantic request/response models
  api/           routers
  core/          auth, security, shared helpers
```
