# Playto Payout Engine (FastAPI)

Minimal payout engine with ledger accounting, row-level locking, idempotent payout requests, and async worker processing.

## Stack

- FastAPI + SQLAlchemy 2.0 (async)
- PostgreSQL via `asyncpg`
- Celery worker
- Ledger-based accounting (no balance column)

## Run Locally

1. Create a PostgreSQL database.
2. Configure `.env`:
   - `DATABASE_URL=postgresql+asyncpg://...`
   - `CELERY_BROKER_URL=redis://...` (or RabbitMQ URL if configured)
   - `CELERY_RESULT_BACKEND=redis://...`
3. Install dependencies:
   - `pip install -e .`
4. Initialize schema + seed data:
   - `python -m db.init_db`
5. Start API:
   - `uvicorn main:app --reload --port 8000`
6. Start worker:
   - `celery -A workers.celery_app.celery_app worker -l info`

## API Endpoints

- `GET /api/v1/merchants`
- `GET /api/v1/merchants/{merchant_id}`
- `GET /api/v1/merchants/{merchant_id}/balance`
- `GET /api/v1/merchants/{merchant_id}/ledger`
- `POST /api/v1/payouts?merchant_id=<uuid>` with `Idempotency-Key` header
- `GET /api/v1/payouts?merchant_id=<uuid>`
- `GET /api/v1/payouts/{payout_id}`

## Testing

- `pytest -q`
- Includes:
  - idempotency replay test (`tests/test_idempotency.py`)
  - concurrent payout race test (`tests/test_payout_concurrency.py`)
