import pandas as pd
import streamlit as st

# Import your existing modules here
# Adjust function names to match your actual code
from mev_types.arbitrage import calculate_arbitrage
from mev_types.frontrun import detect_front_running
from mev_types.sandwich import detect_sandwich_attacks
from blockchain_fetcher import BlockchainFetcher


st.set_page_config(page_title="MEV Detection Tool", layout="wide")

st.title("MEV Detection Tool")

mode = st.sidebar.selectbox(
    "Input type",
    ["Transaction Hash", "Block Range", "CSV Upload"]
)

if mode == "Transaction Hash":
    mev_type_options = ["arbitrage"]
else:
    mev_type_options = ["arbitrage", "frontrun", "sandwich"]

mev_type = st.sidebar.selectbox(
    "MEV type",
    mev_type_options
)

def run_detection(mev_type: str, data):
    if mev_type == "arbitrage":
        return calculate_arbitrage(data)

    if mev_type == "frontrun":
        return detect_front_running(data)

    if mev_type == "sandwich":
        return detect_sandwich_attacks(data)

    raise ValueError(f"Unsupported MEV type: {mev_type}")


if mode == "Transaction Hash":
    tx_hash = st.text_input("Transaction hash")

    if st.button("Analyze transaction"):
        if not tx_hash:
            st.error("Enter a transaction hash.")
        else:
            fetcher = BlockchainFetcher()
            tx = fetcher.fetch_transfer_by_tx(tx_hash)

            results = run_detection(mev_type, tx)

            st.subheader("Results")
            st.dataframe(pd.DataFrame(results), use_container_width=True)


elif mode == "Block Range":
    block_number = st.number_input("Block number", min_value=0, step=1)
    start = st.number_input("Start transaction index", min_value=0, step=1)
    end = st.number_input("End transaction index", min_value=0, step=1)

    if st.button("Analyze block range"):
        if end <= start:
            st.error("End index must be greater than start index.")
        else:
            fetcher = BlockchainFetcher()
            txs = fetcher.fetch_block_transactions(
                block_number=int(block_number),
                start=int(start),
                end=int(end),
            )

            all_results = []

            for tx in txs:
                results = run_detection(mev_type, tx)
                if results:
                    all_results.extend(results)

            st.subheader("Results")
            st.dataframe(pd.DataFrame(all_results), use_container_width=True)


elif mode == "CSV Upload":
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.subheader("Uploaded Data")
        st.dataframe(df, use_container_width=True)

        if st.button("Analyze CSV"):
            results = run_detection(mev_type, df)

            st.subheader("Results")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
