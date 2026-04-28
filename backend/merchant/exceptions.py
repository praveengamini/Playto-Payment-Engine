class MerchantNotFoundError(Exception):
    def __init__(self, merchant_id: str):
        super().__init__(f"Merchant not found: {merchant_id}")
        self.merchant_id = merchant_id