from collections import defaultdict
from typing import List, Dict, Any


def detect_front_running(transactions: List) -> List[Dict[str, Any]]:
    """
    Detect simple front-running patterns from ordered on-chain swaps.

    Heuristic idea:
    - A "bot" (earlier tx) trades in the same pool before a "victim"
    - Both interact with same token pair (same pool)
    - Bot benefits from price movement caused by victim's larger trade
    """

    frontruns = []

    # ----------------------------------------
    # Group swaps by pool
    # ----------------------------------------
    pool_swaps = defaultdict(list)

    for tx in transactions:
        if not hasattr(tx, "swaps") or not tx.swaps:
            continue

        for swap in tx.swaps:
            pool = swap.get("pool")
            if not pool:
                continue

            pool_swaps[pool].append({
                "tx": tx,
                "swap": swap,
                "block_index": getattr(tx, "block_index", 0),
                "price": swap.get("price"),
                "direction": swap.get("direction"),
                "amount_in": swap.get("amount_in"),
            })

    # ----------------------------------------
    # Detect frontruns per pool
    # ----------------------------------------
    for pool, swaps in pool_swaps.items():
        # ensure deterministic order
        swaps.sort(key=lambda x: x["block_index"])

        n = len(swaps)

        for i in range(n):
            bot = swaps[i]

            for j in range(i + 1, n):
                victim = swaps[j]

                # skip if missing data
                if bot["price"] is None or victim["price"] is None:
                    continue

                # ----------------------------------------
                # Condition 1: same pool already ensured
                # ----------------------------------------

                # ----------------------------------------
                # Condition 2: bot trades BEFORE victim
                # ----------------------------------------
                if bot["block_index"] >= victim["block_index"]:
                    continue

                # ----------------------------------------
                # Condition 3: victim is large enough to move price
                # ----------------------------------------
                try:
                    victim_size = float(victim["amount_in"] or 0)
                    bot_size = float(bot["amount_in"] or 0)
                except Exception:
                    continue

                if victim_size <= bot_size:
                    continue  # ignore noise / non-impactful trades

                # ----------------------------------------
                # Condition 4: price movement benefit
                # ----------------------------------------
                bot_price = bot["price"]
                victim_price = victim["price"]

                price_change = victim_price - bot_price

                # bot benefits if price moves in same direction
                if abs(price_change) / (bot_price + 1e-9) < 0.01:
                    continue  # ignore negligible movement

                frontruns.append({
                    "pool": pool,
                    "bot_tx": bot["tx"].tx_hash,
                    "victim_tx": victim["tx"].tx_hash,
                    "bot_block_index": bot["block_index"],
                    "victim_block_index": victim["block_index"],
                    "bot_price": bot_price,
                    "victim_price": victim_price,
                    "price_change": price_change,
                    "bot_direction": bot["direction"],
                    "victim_direction": victim["direction"],
                })

    return frontruns