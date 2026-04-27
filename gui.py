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

mode = st.sidebar.selectbox(
    "Input type",
    ["Transaction Hash", "Block", "CSV Upload"]
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

        st.subheader("Results")

        if all_results:
            st.dataframe(pd.DataFrame(all_results), use_container_width=True)
        else:
            st.warning("No MEV pattern detected.")


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
