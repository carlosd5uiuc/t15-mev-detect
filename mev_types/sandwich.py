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

            swap = dict(s)
            swap["block_index"] = getattr(tx, "block_index", None)

            swaps.append(swap)

    swaps.sort(key=lambda x: x["transactionIndex"] if x["transactionIndex"] is not None else 999999)

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

            # victim must be different from attacker
            if mid["trader"] == first["trader"]:
                continue

            # price logic (simple validation)
            if None in (first["price"], mid["price"], last["price"]):
                continue

            price_up = mid["price"] > first["price"]
            price_down = last["price"] < mid["price"]

            if price_up and price_down:
                profit = None
                profit_token = None

                # Validate attacker round trip:
                # bot_buy:  token A -> token B
                # bot_sell: token B -> token A
                if (
                    first["token_in"] == last["token_out"]
                    and first["token_out"] == last["token_in"]
                ):
                    profit_token = first["token_in"]
                    profit = last["amount_out"] - first["amount_in"]

                results.append({
                    "pool": pool,
                    "attacker": first["trader"],
                    "victim": mid["trader"],

                    "bot_buy": first,
                    "victim_swap": mid,
                    "bot_sell": last,

                    "profit_token": profit_token,
                    "gross_profit": profit,

                    "front_tx_hash": first["tx_hash"],
                    "victim_tx_hash": mid["tx_hash"],
                    "back_tx_hash": last["tx_hash"],

                    "front_index": first["transactionIndex"],
                    "victim_index": mid["transactionIndex"],
                    "back_index": last["transactionIndex"],
                })

    return results
