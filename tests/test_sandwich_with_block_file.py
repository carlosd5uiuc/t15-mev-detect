import json
import subprocess
from pathlib import Path

BLOCK_FILE = Path("blocks.json")

with BLOCK_FILE.open("r") as f:
    block_ids = json.load(f)

non_empty_count = 0
empty_count = 0

for i, block_id in enumerate(block_ids):
    print(f"\nRunning index {i}: block {block_id}")

    result = subprocess.run(
        ["python", "blockchain_fetcher.py", "sandwich", str(block_id)],
        text=True,
        capture_output=True
    )

    output = result.stdout.strip()

    if output:
        print(output)

    if result.stderr:
        print("ERROR:")
        print(result.stderr)

    # Count non-empty arrays
    if output == "[]":
        empty_count += 1
    else:
        non_empty_count += 1

print("\nSummary")
print(f"Non-empty arrays: {non_empty_count}/{len(block_ids)}")
print(f"Empty arrays: {empty_count}/{len(block_ids)}")
