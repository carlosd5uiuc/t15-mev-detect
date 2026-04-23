from collections import defaultdict
from typing import List


def detect_sandwich_attacks(transactions: List):
    """
    Detect simple sandwich patterns using API-based block data:

        bot_tx (buy) → victim_tx → bot_tx (sell)

    NOTE:
    This is heuristic-based (no swap decoding).
    """

    # 1. group transactions by block
    blocks = defaultdict(list)

    for tx in transactions:
        if tx.block_height is None:
            continue
        blocks[tx.block_height].append(tx)

    sandwiches = []

    # 2. analyze each block
    for block, txs in blocks.items():

        # order by time (approx execution order)
        txs.sort(key=lambda x: x.timestamp or 0)

        # need at least 3 txs
        if len(txs) < 3:
            continue

        # sliding window: bot → victim → bot
        for i in range(1, len(txs) - 1):

            tx_prev = txs[i - 1]
            tx_mid = txs[i]
            tx_next = txs[i + 1]

            # -----------------------------
            # BASIC FILTERS (same DEX / contract)
            # -----------------------------
            if (
                tx_prev.to_addr != tx_mid.to_addr or
                tx_mid.to_addr != tx_next.to_addr
            ):
                continue

            # ignore zero-value noise txs
            if int(tx_mid.value or 0) == 0:
                continue

            # -----------------------------
            # SANDWICH HEURISTIC
            # -----------------------------
            # bot pays higher gas → victim normal → bot pays higher again
            if (
                int(tx_prev.gasPrice or 0) > int(tx_mid.gasPrice or 0) and
                int(tx_next.gasPrice or 0) > int(tx_mid.gasPrice or 0)
            ):
                sandwiches.append({
                    "block": block,
                    "bot_front_run": tx_prev.tx_hash,
                    "victim": tx_mid.tx_hash,
                    "bot_back_run": tx_next.tx_hash,
                    "contract": tx_mid.to_addr,
                })

    return sandwiches