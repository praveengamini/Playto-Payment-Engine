# Postman Testing Guide

This document provides a clean Postman flow to test the Playto Payout Engine APIs.

## 1) Base Setup

- Base URL: `http://localhost:8000`
- Headers for JSON requests:
  - `Content-Type: application/json`
- Use merchant IDs from seed data:
  - `11111111-1111-1111-1111-111111111111`
  - `22222222-2222-2222-2222-222222222222`
  - `33333333-3333-3333-3333-333333333333`

## 2) Recommended Postman Environment Variables

Create a Postman environment with:

- `base_url` = `http://localhost:8000`
- `merchant_id` = `11111111-1111-1111-1111-111111111111`
- `bank_account_id` = `BANK-ARJUN-001`
- `idempotency_key` = (set manually to a UUID v4 for each new payout)
- `payout_id` = (filled after create payout response)

## 3) Core API Requests

### A) List Merchants

- Method: `GET`
- URL: `{{base_url}}/api/v1/merchants`

### B) Get Merchant Details

- Method: `GET`
- URL: `{{base_url}}/api/v1/merchants/{{merchant_id}}`

### C) Get Merchant Balance

- Method: `GET`
- URL: `{{base_url}}/api/v1/merchants/{{merchant_id}}/balance`

Expected fields include:
- `available_paise`
- `held_paise`
- `total_credited_paise`
- `total_debited_paise`

### D) Get Merchant Ledger

- Method: `GET`
- URL: `{{base_url}}/api/v1/merchants/{{merchant_id}}/ledger?limit=50`

## 4) Payout Flow Tests

### E) Create Payout (First Request)

- Method: `POST`
- URL: `{{base_url}}/api/v1/payouts?merchant_id={{merchant_id}}`
- Headers:
  - `Idempotency-Key: {{idempotency_key}}`
  - `Content-Type: application/json`
- Body (raw JSON):

```json
{
  "amount_paise": 6000,
  "bank_account_id": "{{bank_account_id}}"
}
```

Expected:
- `200 OK`
- Response contains payout object with `status: "pending"` initially.

### F) Idempotency Replay Test (Same Key, Same Body)

Send the exact same request again:
- Method: `POST`
- URL: `{{base_url}}/api/v1/payouts?merchant_id={{merchant_id}}`
- Same `Idempotency-Key`
- Same body

Expected:
- `200 OK`
- Same payout `id` as first request (no duplicate payout row).

### G) New Payout With New Idempotency Key

Change `idempotency_key` to a new UUID and submit again.

Expected:
- New payout `id` (unless insufficient available balance).

### H) Insufficient Balance Check

Try a very large amount:

```json
{
  "amount_paise": 999999999,
  "bank_account_id": "{{bank_account_id}}"
}
```

Expected:
- `409 Conflict`
- Error message indicates insufficient balance.

## 5) Payout Tracking Requests

### I) List Merchant Payouts

- Method: `GET`
- URL: `{{base_url}}/api/v1/payouts?merchant_id={{merchant_id}}&limit=50`

### J) Get Payout By ID

- Method: `GET`
- URL: `{{base_url}}/api/v1/payouts/{{payout_id}}`

Use this after saving `payout_id` from the create response.

## 6) Optional Worker Testing (Lifecycle)

If Celery worker is running, payout status moves from `pending` to:
- `processing`
- then `completed` or `failed` (or temporarily hangs in `processing`)

Re-run:
- `GET /api/v1/payouts/{{payout_id}}`
- `GET /api/v1/merchants/{{merchant_id}}/balance`

On failure, held funds should be released back to available balance.

## 7) Postman Test Scripts (Optional)

Use in the **Tests** tab of create payout request:

```javascript
pm.test("Status is 200", function () {
  pm.response.to.have.status(200);
});

const json = pm.response.json();
pm.environment.set("payout_id", json.id);
pm.test("Payout id exists", function () {
  pm.expect(json.id).to.be.a("string");
});
```

Use in idempotency replay request:

```javascript
pm.test("Status is 200", function () {
  pm.response.to.have.status(200);
});
const json = pm.response.json();
pm.test("Replay returns same payout id", function () {
  pm.expect(json.id).to.eql(pm.environment.get("payout_id"));
});
```

## 8) Concurrency Test in Postman Runner (Manual Approximation)

Postman cannot perfectly reproduce DB-level races like a dedicated concurrency test, but you can approximate:

1. Create two requests with different `Idempotency-Key` values.
2. Use amount close to available balance (for example two requests of `6000` when available is around `10000`).
3. Send both quickly via Runner.

Expected behavior:
- One payout succeeds.
- One request fails with `409` due to insufficient balance.

## 9) Common Failures

- `422 Idempotency-Key must be a valid UUID v4`
  - Use a proper UUID v4 in header.
- `404 Merchant not found`
  - Verify `merchant_id` exists in DB.
- Connection refused
  - Ensure API is running: `uvicorn main:app --reload --port 8000`
