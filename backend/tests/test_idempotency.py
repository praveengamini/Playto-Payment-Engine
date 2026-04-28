import uuid


async def test_same_idempotency_key_returns_same_payout(api_client, seeded_merchant):
    key = str(uuid.uuid4())
    payload = {"amount_paise": 3000, "bank_account_id": "BANK-TEST-001"}

    first = await api_client.post(
        f"/api/v1/payouts?merchant_id={seeded_merchant}",
        headers={"Idempotency-Key": key},
        json=payload,
    )
    assert first.status_code == 200, first.text
    first_body = first.json()

    second = await api_client.post(
        f"/api/v1/payouts?merchant_id={seeded_merchant}",
        headers={"Idempotency-Key": key},
        json=payload,
    )
    assert second.status_code == 200, second.text
    second_body = second.json()

    assert first_body["id"] == second_body["id"]
    assert first_body["idempotency_key"] == second_body["idempotency_key"] == key
