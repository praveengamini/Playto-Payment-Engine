import asyncio
import uuid


async def test_parallel_payout_requests_only_one_succeeds(api_client, seeded_merchant):
    payload = {"amount_paise": 6000, "bank_account_id": "BANK-TEST-001"}
    key_1 = str(uuid.uuid4())
    key_2 = str(uuid.uuid4())

    async def create(key: str):
        return await api_client.post(
            f"/api/v1/payouts?merchant_id={seeded_merchant}",
            headers={"Idempotency-Key": key},
            json=payload,
        )

    response_1, response_2 = await asyncio.gather(create(key_1), create(key_2))
    codes = sorted([response_1.status_code, response_2.status_code])


    assert codes == [200, 409]
