from collections import defaultdict

def detect_sandwich_attacks(transactions):

    swaps = []

    # ----------------------------
    # FLATTEN
    # ----------------------------
    for tx in transactions:
        for s in getattr(tx, "swaps", []):
            if not s:
                continue

            swaps.append({
                "tx_hash": s["tx_hash"],
                "pool": s["pool"],
                "trader": s.get("trader"),
                "price": s.get("price"),
                "direction": s.get("direction"),
                "block_index": getattr(tx, "block_index", None),
            })

    swaps.sort(key=lambda x: x["block_index"] or 999999)

    pool_map = defaultdict(list)

    for s in swaps:
        pool_map[s["pool"]].append(s)

    results = []

    # ----------------------------
    # REAL SANDWICH RULE
    # ----------------------------
    for pool, s_list in pool_map.items():

        for i in range(len(s_list) - 2):

            first = s_list[i]
            mid = s_list[i + 1]
            last = s_list[i + 2]

            # must have valid traders
            if not (first["trader"] and last["trader"]):
                continue

            # SAME BOT MUST FRONT AND BACK RUN
            if first["trader"] != last["trader"]:
                continue

            # victim must be different
            if mid["trader"] == first["trader"]:
                continue

            # price logic (simple validation)
            if None in (first["price"], mid["price"], last["price"]):
                continue

            price_up = mid["price"] > first["price"]
            price_down = last["price"] < mid["price"]

            if price_up and price_down:
                results.append({
                    "pool": pool,
                    "attacker": first["trader"],
                    "victim": mid["trader"],
                    "bot_buy": first,
                    "victim_swap": mid,
                    "bot_sell": last,
                })

    return results