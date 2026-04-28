# Playto Founding Engineer Challenge — EXPLAINER

This file answers the questions from the challenge problem statement and points to the concrete code paths in this repo.

## Implementation note

The problem statement names Django + DRF for the backend stack. This submission uses **FastAPI + SQLAlchemy (async)** for the API layer while preserving the same engineering guarantees required by the challenge:

- **PostgreSQL + DB-enforced concurrency**: row-level locks (`SELECT ... FOR UPDATE`) and balance aggregation are executed in the database.
- **Background processing**: Celery worker performs payout lifecycle simulation + retries.
- **Ledger integrity**: balances are derived from an append-only ledger in paise (`BigInteger`), never floats.

Reason for this choice:
- I optimized for **correctness and speed of iteration** in a time-boxed exercise using a stack I can reason about confidently under transaction and locking pressure.
- The core requirements being evaluated here, such as locking, atomicity, idempotency, invariants, and retries, are **stack-agnostic** and are implemented explicitly.

If this were implemented in Django/DRF instead, the core design would remain the same: the same SQL aggregation, the same `SELECT ... FOR UPDATE`, and the same unique idempotency constraint would apply.

## 1) The Ledger

### Balance calculation query (from code)

All balance math is done **in PostgreSQL**, not in Python, using conditional aggregation (CASE WHEN).

Source: `backend/ledger/repository.py` (`get_available_balance_for_update` and `get_balance_breakdown`).

The “available” query shape is:

```sql
SELECT COALESCE(SUM(
  CASE
    WHEN entry_type = 'credit'       THEN  amount_paise
    WHEN entry_type = 'hold_release' THEN  amount_paise
    WHEN entry_type = 'debit'        THEN -amount_paise
    WHEN entry_type = 'hold'         THEN -amount_paise
    ELSE 0
  END
), 0) AS available_paise
FROM ledger_entries
WHERE merchant_id = :merchant_id;
```

### Why model credits/debits/holds this way?

- **Append-only ledger** (`credit`, `hold`, `hold_release`, `debit`) gives an auditable trail and prevents “drift” bugs from a mutable balance column.
- **Holds** are the concurrency-safe way to reserve funds at request time while the payout is still pending/processing.
- The key invariant becomes checkable:
  - \(held = \sum hold - \sum hold\_release\)
  - \(available = \sum credit - \sum debit - held\)

## 2) The Lock

### Exact code that prevents overdraft

Source: `backend/payout/service.py` (`request_payout`).

We lock the merchant row before computing balance + inserting a HOLD:

```python
result = await session.execute(
    select(Merchant)
    .where(Merchant.id == merchant_id)
    .with_for_update()
)
```

### What DB primitive this relies on

This relies on PostgreSQL row locks via **`SELECT ... FOR UPDATE`**. Competing payout requests for the same merchant **serialize** at the database level:

- T1 locks merchant row → computes balance → inserts HOLD → commits
- T2 blocks on the same row lock → then computes a post-T1 balance and either succeeds or cleanly fails with insufficient funds

This avoids the classic check-then-deduct race.

## 3) The Idempotency

### How the system knows it has seen a key before

There’s an `idempotency_records` table:

- Code: `backend/idempotency/model.py`
- Uniqueness: composite unique index on (`merchant_id`, `idempotency_key`)
- Expiry: `expires_at` with TTL set to **24h** via `IDEMPOTENCY_TTL_SECONDS=86400` (`backend/core/config.py`)

### What happens if request #1 is in-flight when request #2 arrives?

Source: `backend/payout/service.py` (`request_payout`).

The flow is intentionally **double-checked**:

1. **Fast-path check** before taking the lock (good latency for normal duplicates)
2. Acquire the merchant row lock (`FOR UPDATE`)
3. **Re-check idempotency after the lock**
4. Only then compute balance, create payout, insert HOLD, and store response

That post-lock re-check closes the race window where two concurrent requests could both pass an early idempotency check before the first commits.

## 4) The State Machine

### Where illegal transitions are blocked

Source: `backend/payout/service.py` (`transition_status`).

```python
if not is_legal_transition(current, new_status):
    raise InvalidStateTransitionError(payout_id, current.value, new_status.value)
```

Allowed:
- `pending -> processing -> completed`
- `pending -> processing -> failed`

Blocked:
- any backward transition
- any terminal-to-active transition (e.g. failed → completed)

### Atomic funds behavior on transitions

Source: `backend/payout/service.py`

- `complete_payout`: status → `completed` and HOLD → DEBIT in the **same transaction**
- `fail_payout`: status → `failed` and HOLD → HOLD_RELEASE in the **same transaction**

## 5) The AI Audit

### One specific subtle bug from AI-generated code

**Bug**: AI suggested checking idempotency only before acquiring the merchant lock. Under concurrent duplicate requests, both requests can pass the pre-check before either commits, resulting in two payouts.

**Fix in this repo**: keep the pre-check, but add a second idempotency check **after** `SELECT ... FOR UPDATE` lock acquisition inside `request_payout`.

Source: `backend/payout/service.py`:

- `existing = await check_idempotency(...)` (fast-path)
- lock merchant row
- `existing_after_lock = await check_idempotency(...)` (race-window closer)

This preserves latency while making the duplicate-in-flight case safe.

## Open to the suggested stack

I’m fully open to implementing this service in the problem statement’s suggested backend stack (Django + DRF) as well.
The core design and safety properties would remain the same: append-only ledger + database aggregation, `SELECT ... FOR UPDATE`
for concurrency control, a unique per-merchant idempotency record with TTL, and atomic state transitions with ledger writes in a single transaction.
