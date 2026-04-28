const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch {
    throw new Error(
      `Network error: cannot reach API at ${API_BASE_URL}. Ensure backend is running and CORS is configured.`
    );
  }
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message = typeof payload === "object" && payload?.detail ? payload.detail : "Request failed";
    throw new Error(message);
  }

  return payload;
}

export async function fetchMerchants() {
  return request("/api/v1/merchants");
}

export async function fetchBalance(merchantId) {
  return request(`/api/v1/merchants/${merchantId}/balance`);
}

export async function fetchLedger(merchantId, limit = 25) {
  return request(`/api/v1/merchants/${merchantId}/ledger?limit=${limit}`);
}

export async function fetchPayouts(merchantId, limit = 25) {
  return request(`/api/v1/payouts?merchant_id=${merchantId}&limit=${limit}`);
}

export async function createPayout({
  merchantId,
  amountPaise,
  bankAccountId,
  idempotencyKey,
}) {
  return request(`/api/v1/payouts?merchant_id=${merchantId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify({
      amount_paise: amountPaise,
      bank_account_id: bankAccountId,
    }),
  });
}
