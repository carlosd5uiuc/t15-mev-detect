import networkx as nx

def build_directed_graph(transfers):
    g = nx.DiGraph()
    for t in transfers:
        g.add_edge(
            t["from"],
            t["to"],
            token=t["token"],
            amount=t["value"]
        )
    return g

def build_scss_list(d_graph):
    return list(nx.strongly_connected_components(d_graph))

def build_pnl_table(sccs, transfers):
    from collections import defaultdict
    component = sccs[0]
    pnl = defaultdict(lambda: defaultdict(float))
    for t in transfers:
        if t["from"] in component and t["to"] in component:
            pnl[t["from"]][t["token"]] -= t["value"]
            pnl[t["to"]][t["token"]] += t["value"]
    return pnl

def extract_arbitrageurs(pnl_table, tol=1e-3):
    arbitrageurs = []

    for address, token_balances in pnl_table.items():
        has_near_zero = any(abs(v) <= tol for v in token_balances.values())

        if has_near_zero:
            for token, value in token_balances.items():
                if abs(value) > tol:
                    arbitrageurs.append({
                        "address": address,
                        "token": token,
                        "value": value,
                    })

    return arbitrageurs


def calculate_arbitrage(transfers):
    directed_graph = build_directed_graph(transfers)
    sccs_list = build_scss_list(directed_graph)
    pnl = build_pnl_table(sccs_list, transfers)
    result = extract_arbitrageurs(pnl)
    return result
