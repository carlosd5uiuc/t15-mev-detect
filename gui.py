from xmlrpc import client

import pandas as pd
import streamlit as st

# Import your existing modules here
# Adjust function names to match your actual code
from mev_types.arbitrage import calculate_arbitrage
from mev_types.frontrun import detect_front_running
from mev_types.sandwich import detect_sandwich_attacks
from blockchain_fetcher import BlockchainFetcher
from receipt_cache import get_block_receipts, _cache_path


st.set_page_config(page_title="MEV Detection Tool", layout="wide")

st.title("MEV Detection Tool")
if "arbitrage_rows" not in st.session_state:
    st.session_state.arbitrage_rows = []

if "sandwich_rows" not in st.session_state:
    st.session_state.sandwich_rows = []

if "last_mode" not in st.session_state:
    st.session_state.last_mode = None

input_col, mev_col = st.columns(2)

with input_col:
    mode = st.selectbox(
        "Input type",
        ["Transaction Hash", "Block"]
    )

if st.session_state.last_mode != mode:
    st.session_state.arbitrage_rows = []
    st.session_state.last_mode = mode

if mode == "Transaction Hash":
    mev_type_options = ["Arbitrage"]
else:
    mev_type_options = ["Arbitrage", "Sandwich"]

with mev_col:
    mev_type = st.selectbox(
        "MEV type",
        mev_type_options
    )

def display_arbitrage_table(rows, fetcher):
    df = format_arbitrage_results(rows, fetcher)
    visible_df = df.drop(columns=["Full Transaction Hash", "Arbitrageur", "Full Arbitrageur Address"])

    table_col, detail_col = st.columns([1, 1])

    with table_col:
        event = st.dataframe(
            visible_df,
            width="stretch",
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )

    with detail_col:
        st.subheader("Transaction Details")

        selected_rows = event.selection.rows

        if not selected_rows:
            st.info("Select a row to view details.")
            return

        selected_index = selected_rows[0]
        selected = df.iloc[selected_index]

        with st.container(border=True):
            st.write("**Full Transaction Hash**")
            st.code(selected["Full Transaction Hash"])

            st.write("**Arbitrageur**")
            st.code(selected["Full Arbitrageur Address"])

            st.write("**Token**")
            st.code(selected["Token"])

            st.write("**Net Amount**")
            st.code(str(selected["Net Amount"]))

def run_detection(mev_type: str, data):
    if mev_type == "Arbitrage":
        return calculate_arbitrage(data)

    if mev_type == "frontrun":
        return detect_front_running(data)

    if mev_type == "Sandwich":
        return detect_sandwich_attacks(data)

    raise ValueError(f"Unsupported MEV type: {mev_type}")

def shorten_hash(value: str) -> str:
    if not value:
        return ""

    if len(value) <= 16:
        return value

    return f"{value[:10]}...{value[-8:]}"

def format_arbitrage_results(rows, fetcher):
    formatted_rows = []

    for row in rows:
        token_address = row["token"]
        token_symbol = fetcher.get_token_symbol(token_address)

        formatted_rows.append({
            "Transaction": shorten_hash(row["tx"]),
            "Full Transaction Hash": row["tx"],
            "Arbitrageur": shorten_hash(row["address"]),
            "Full Arbitrageur Address": row["address"],
            "Token": token_symbol,
            "Net Amount": round(row["value"], 6),
        })

    return pd.DataFrame(formatted_rows)


def format_sandwich_results(rows):
    formatted = []

    for row in rows:
        bot_buy = row["bot_buy"]
        victim_swap = row["victim_swap"]
        bot_sell = row["bot_sell"]

        formatted.append({
            "Pool": row["pool"],

            "Attacker": row["attacker"][:10] + "...",
            "Full Attacker Address": row["attacker"],

            "Victim": row["victim"][:10] + "...",
            "Full Victim Address": row["victim"],

            "Front Tx": bot_buy["tx_hash"][:10] + "...",
            "Full Front Tx Hash": bot_buy["tx_hash"],

            "Victim Tx": victim_swap["tx_hash"][:10] + "...",
            "Full Victim Tx Hash": victim_swap["tx_hash"],

            "Back Tx": bot_sell["tx_hash"][:10] + "...",
            "Full Back Tx Hash": bot_sell["tx_hash"],

            "Front Index": bot_buy["transactionIndex"],
            "Victim Index": victim_swap["transactionIndex"],
            "Back Index": bot_sell["transactionIndex"],

            "Front Price": bot_buy["price"],
            "Victim Price": victim_swap["price"],
            "Back Price": bot_sell["price"],

            "Profit Token": row.get("profit_token"),
            "Gross Profit": row.get("gross_profit"),
        })

    return pd.DataFrame(formatted)

def display_sandwich_table(rows):
    df = format_sandwich_results(rows)

    hidden_cols = [
        "Full Attacker Address",
        "Full Victim Address",
        "Full Front Tx Hash",
        "Full Victim Tx Hash",
        "Full Back Tx Hash",
    ]

    visible_df = df.drop(columns=hidden_cols)

    table_col, detail_col = st.columns([1, 1])

    with table_col:
        event = st.dataframe(
            visible_df,
            width="stretch",
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )

    with detail_col:
        st.subheader("Sandwich Details")

        selected_rows = event.selection.rows

        if not selected_rows:
            st.info("Select a row to view details.")
            return

        selected_index = selected_rows[0]
        selected = df.iloc[selected_index]

        with st.container(border=True):
            st.write("**Pool**")
            st.code(selected["Pool"])

            st.write("**Attacker**")
            st.code(selected["Full Attacker Address"])

            st.write("**Victim**")
            st.code(selected["Full Victim Address"])

            st.write("**Front-run Transaction**")
            st.code(selected["Full Front Tx Hash"])

            st.write("**Victim Transaction**")
            st.code(selected["Full Victim Tx Hash"])

            st.write("**Back-run Transaction**")
            st.code(selected["Full Back Tx Hash"])

            st.write("**Transaction Order**")
            st.code(
                f'{selected["Front Index"]} -> '
                f'{selected["Victim Index"]} -> '
                f'{selected["Back Index"]}'
            )

            st.write("**Price Movement**")
            st.code(
                f'{selected["Front Price"]} -> '
                f'{selected["Victim Price"]} -> '
                f'{selected["Back Price"]}'
            )

            st.write("**Profit Token**")
            st.code(str(selected["Profit Token"]))

            st.write("**Gross Profit**")
            st.code(str(selected["Gross Profit"]))


if mode == "Transaction Hash":
    tx_hash = st.text_input("Transaction hash")

    if st.button("Analyze transaction"):
        if not tx_hash:
            st.error("Enter a transaction hash.")
            st.session_state.arbitrage_rows = []
        else:
            fetcher = BlockchainFetcher()
            transfers = fetcher.fetch_transfer_by_tx(tx_hash)

            results = run_detection(mev_type, transfers)

            table_data = []

            for item in results:
                table_data.append({
                    "tx": tx_hash,
                    "address": item["address"],
                    "token": item["token"],
                    "value": item["value"],
                })

            st.session_state.arbitrage_rows = table_data

            if not table_data:
                st.warning("No MEV pattern detected.")

    if st.session_state.arbitrage_rows:
        fetcher = BlockchainFetcher()
        st.subheader("Results")
        display_arbitrage_table(st.session_state.arbitrage_rows, fetcher)


elif mode == "Block":
    block_number = st.number_input("Block number", min_value=0, step=1)

    if st.button("Analyze block"):
        if mev_type == "Arbitrage":
            with st.spinner("Analyzing block..."):
                fetcher = BlockchainFetcher()

                tx_transfers = fetcher.fetch_transfers_by_block_from_cache(
                    block_number=int(block_number)
                )

                all_results = []

                for tx_hash, transfers in tx_transfers.items():
                    results = run_detection(mev_type, transfers)

                    if results:
                        for item in results:
                            all_results.append({
                                "tx": tx_hash,
                                "address": item["address"],
                                "token": item["token"],
                                "value": item["value"],
                            })

                st.session_state.arbitrage_rows = all_results

                if not all_results:
                    st.warning("No MEV pattern detected.")

        elif mev_type == "Sandwich":
            with st.spinner("Analyzing block..."):
                fetcher = BlockchainFetcher()
                txs = fetcher.fetch_block_transactions(block_number)

                results = detect_sandwich_attacks(txs)

                st.session_state.sandwich_rows = results

                if not results:
                    st.warning("No sandwich attacks detected.")
            
    if mev_type == "Arbitrage" and st.session_state.arbitrage_rows:
        fetcher = BlockchainFetcher()
        st.subheader("Results")
        display_arbitrage_table(st.session_state.arbitrage_rows, fetcher)

    elif mev_type == "Sandwich" and st.session_state.sandwich_rows:
        st.subheader("Results")
        display_sandwich_table(st.session_state.sandwich_rows)


elif mode == "CSV Upload":
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.subheader("Uploaded Data")
        st.dataframe(df, width='stretch')

        if st.button("Analyze CSV"):
            results = run_detection(mev_type, df)

            st.subheader("Results")
            st.dataframe(pd.DataFrame(results), width='stretch')
