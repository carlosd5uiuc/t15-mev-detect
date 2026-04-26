from receipt_cache import get_block_receipts


block_number = 24558873

payload = get_block_receipts(block_number)

print("Block:", payload["blockNumber"])
print("Block hash:", payload["blockHash"])
print("Receipt count:", payload["receiptCount"])
print("First tx hash:", next(iter(payload["receipts"])))
