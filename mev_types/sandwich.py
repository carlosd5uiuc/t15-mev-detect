def detect_sandwich_attacks(transactions):
    """
    Detect sandwich attacks from decoded transactions.
    """

    swaps = []

    for tx in transactions:
        for swap in getattr(tx, "swaps", []):
            if not swap:
                continue

            swaps.append({
                "tx_hash": swap["tx_hash"],
                "pool": swap["pool"],
                "direction": swap.get("direction"),
                "price": swap.get("price"),
                "block_index": getattr(tx, "block_index", None),
            })

    # sort execution order
    swaps.sort(key=lambda x: x["block_index"])

    pool_map = {}

    for s in swaps:
        pool_map.setdefault(s["pool"], []).append(s)

    results = []

    for pool, s_list in pool_map.items():

        for i in range(len(s_list) - 2):

            a, b, c = s_list[i], s_list[i+1], s_list[i+2]

            if None in (a["price"], b["price"], c["price"]):
                continue

            # -------------------------
            # PRICE IMPACT CHECK
            # -------------------------
            price_spike = a["price"] < b["price"]
            price_revert = c["price"] < b["price"]

            if price_spike and price_revert:
                results.append({
                    "pool": pool,
                    "bot_buy": a,
                    "victim": b,
                    "bot_sell": c
                })

    return results