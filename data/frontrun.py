from collections import defaultdict
from typing import List, Dict, Any


def safe_int(x):
    return int(x) if x is not None else 0


def detect_front_running(transactions: List):
    """
    Detect simple front-running / sandwich-like patterns:

    pattern:
        fast_tx → victim_tx → fast_tx
    inside same block + same general contract interaction
    """

    # Step 1: group transactions by block
    blocks = defaultdict(list)

    for tx in transactions:
        if tx.block_height is None:
            continue
        blocks[tx.block_height].append(tx)

    frontruns = []

    # Step 2: analyze each block
    for block, txs in blocks.items():

        # approximate execution order
        txs.sort(key=lambda x: x.timestamp or 0)

        for i in range(1, len(txs) - 1):

            prev_tx = txs[i - 1]
            curr_tx = txs[i]
            next_tx = txs[i + 1]

            # --- SAFETY CHECKS ---
            if curr_tx.value is None:
                continue

            # ignore zero-value noise txs
            if safe_int(curr_tx.value) == 0:
                continue

            # --- CONTRACT GROUPING (LESS STRICT THAN BEFORE) ---
            # instead of requiring exact match, ensure they're all interacting in same region
            if len({prev_tx.to_addr, curr_tx.to_addr, next_tx.to_addr}) > 1:
                continue

            # --- FRONT-RUNNING PATTERN (GAS AUCTION SIGNATURE) ---
            if (
                safe_int(prev_tx.gasPrice) > safe_int(curr_tx.gasPrice)
                and safe_int(next_tx.gasPrice) > safe_int(curr_tx.gasPrice)
            ):

                frontruns.append({
                    "block": block,
                    "victim": curr_tx.tx_hash,
                    "front_runner_before": prev_tx.tx_hash,
                    "front_runner_after": next_tx.tx_hash,
                    "contract": curr_tx.to_addr,
                })

    return frontruns