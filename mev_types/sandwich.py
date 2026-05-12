def detect_sandwich_attacks(transactions):
    """
    Detect sandwich attacks from decoded transactions.
    """

    # ----------------------------
    # STEP 1: FLATTEN SWAPS
    # ----------------------------
    swaps = []

    for tx in transactions:
        for swap in getattr(tx, "swaps", []):
            swaps.append({
                "tx_hash": swap["tx_hash"],
                "pool": swap["pool"],
                "direction": swap.get("direction"),
                "block_index": getattr(tx, "block_index", None),
                "amount_in": swap.get("amount_in"),
                "amount_out": swap.get("amount_out"),
            })

    # ----------------------------
    # STEP 2: SORT BY EXECUTION ORDER
    # ----------------------------
    swaps.sort(key=lambda x: x["block_index"] if x["block_index"] is not None else 999999)

    # ----------------------------
    # STEP 3: GROUP BY POOL
    # ----------------------------
    from collections import defaultdict

    pool_map = defaultdict(list)

    for s in swaps:
        pool_map[s["pool"]].append(s)

    sandwiches = []

    # ----------------------------
    # STEP 4: SLIDING WINDOW SEARCH
    # ----------------------------
    for pool, pool_swaps in pool_map.items():

        for i in range(len(pool_swaps) - 2):

            first = pool_swaps[i]
            middle = pool_swaps[i + 1]
            last = pool_swaps[i + 2]

            # ----------------------------
            # STEP 5: CHECK PATTERN
            # ----------------------------
            if not (
                first["direction"] == "BUY"
                and middle["direction"] == "BUY"
                and last["direction"] == "SELL"
            ):
                continue

            # ensure same pool already guaranteed

            sandwiches.append({
                "pool": pool,
                "bot_buy": first,
                "victim": middle,
                "bot_sell": last,
            })

    return sandwiches