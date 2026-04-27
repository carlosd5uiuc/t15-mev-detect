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

if "last_mode" not in st.session_state:
    st.session_state.last_mode = None

input_col, mev_col = st.columns(2)

with input_col:
    mode = st.selectbox(
        "Input type",
        ["Transaction Hash", "Block", "CSV Upload"]
    )

if st.session_state.last_mode != mode:
    st.session_state.arbitrage_rows = []
    st.session_state.last_mode = mode

if mode == "Transaction Hash":
    mev_type_options = ["arbitrage"]
else:
    mev_type_options = ["arbitrage", "frontrun", "sandwich"]

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
    if mev_type == "arbitrage":
        return calculate_arbitrage(data)

    if mev_type == "frontrun":
        return detect_front_running(data)

    if mev_type == "sandwich":
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

    if st.session_state.arbitrage_rows:
        fetcher = BlockchainFetcher()
        st.subheader("Results")
        display_arbitrage_table(st.session_state.arbitrage_rows, fetcher)


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
