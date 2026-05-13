import ast
import json
import subprocess
from pathlib import Path

TX_FILE = Path("tx_file.json")

with TX_FILE.open("r") as f:
    rows = json.load(f)

empty_indexes = []

# Tracks tx hashes already processed from sample arbitrage results
processed_result_txs = set()

# From sample arbitrage output
# key: tx
# value: grand total of returned item["value"]
sample_arbitrage_totals = {}

# From output.json
# key: tx_hash
# value: grand total of row["usd_value"]
expected_arbitrage_totals = {}

for i, row in enumerate(rows):
    tx_hash = row["tx_hash"]

    # Always add/update totals from the input JSON
    expected_arbitrage_totals[tx_hash] = (
        expected_arbitrage_totals.get(tx_hash, 0) + row["usd_value"]
    )

    print(f"Running index {i}: {tx_hash}")

    result = subprocess.run(
        ["python", "main.py", "arbitrage", "tx", tx_hash],
        text=True,
        capture_output=True
    )

    if result.returncode != 0:
        continue

    try:
        arr = ast.literal_eval(result.stdout.strip())
    except Exception:
        continue

    if len(arr) == 0:
        empty_indexes.append(i)
        continue

    # If this tx was already processed, skip updating result totals
    # if tx_hash in processed_result_txs:
    #     continue

    # Add/update totals from returned arbitrage result
    for item in arr:
        tx = item["tx"]
        value = abs(item["value"])

        sample_arbitrage_totals[tx] = (
            sample_arbitrage_totals.get(tx, 0) + value
        )

    # Mark this tx_hash as processed only after the full result is processed
    processed_result_txs.add(tx_hash)

print("\nIndexes where returned array length == 0:")
print(empty_indexes)

print(f"\nSummary: {len(empty_indexes)}/{len(rows)} returned empty arrays")

print("\nExpected arbitrage totals from output.json:")
print(json.dumps(expected_arbitrage_totals, indent=2))

print("\nSample arbitrage totals from main.py:")
print(json.dumps(sample_arbitrage_totals, indent=2))

print("\nGrand totals per dictionary:")

expected_grand_total = sum(expected_arbitrage_totals.values())
sample_grand_total = sum(sample_arbitrage_totals.values())

print(f"Expected grand total: {expected_grand_total}")
print(f"Sample grand total: {sample_grand_total}")
