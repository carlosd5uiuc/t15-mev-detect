import os
import logging
import csv
import argparse
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from web3 import Web3

logging.basicConfig(level=logging.INFO)
from mev_types.arbitrage import calculate_arbitrage
from mev_types.frontrun import detect_front_running
from mev_types.sandwich import detect_sandwich_attacks

from token_decimals_cache import load_token_decimals_cache, save_token_decimals_cache
from token_metadata_cache import load_token_metadata_cache, save_token_metadata_cache

load_dotenv()
rpc_url_key = os.getenv("RPC_URL_KEY")

class Transaction:
    def __init__(
        self,
        tx_hash,
        from_addr,
        to_addr,
        block_height=None,
        timestamp=None,
        gas_price=None,
        value=None,
        **kwargs
    ):
        # self.tx_hash = tx_hash if isinstance(tx_hash, str) else tx_hash.hex()
        if isinstance(tx_hash, str):
            self.tx_hash = tx_hash if tx_hash.startswith("0x") else f"0x{tx_hash}"
        else:
            hex_value = tx_hash.hex()
            self.tx_hash = hex_value if hex_value.startswith("0x") else f"0x{hex_value}"
        self.to_addr = to_addr
        self.from_addr = from_addr
        self.to_addr = to_addr

        # MEV fields (optional)
        self.block_height = block_height
        self.timestamp = timestamp
        self.gasPrice = gas_price
        self.value = value

    def __repr__(self):
        return f"Tx({self.tx_hash}, from={self.from_addr}, to={self.to_addr})" 
    
class SwapEvent:
    pass

class BlockchainFetcher:
    def __init__(self):
        self.web3_client = Web3(Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{rpc_url_key}"))
        self.web3_client.is_connected()
        self.TRANSFER_TOPIC = self.web3_client.keccak(text="Transfer(address,address,uint256)").hex()
        self.token_decimals_cache = load_token_decimals_cache()
        self.token_metadata_cache = load_token_metadata_cache()

    def get_token_symbol(self, token_address):
        cache_key = token_address.lower()

        if cache_key in self.token_metadata_cache:
            return self.token_metadata_cache[cache_key].get("symbol", cache_key)

        checksum_address = Web3.to_checksum_address(token_address)

        erc20_abi = [
            {
                "name": "symbol",
                "outputs": [{"type": "string"}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function",
            }
        ]

        token = self.web3_client.eth.contract(
            address=checksum_address,
            abi=erc20_abi,
        )

        try:
            symbol = token.functions.symbol().call()
        except Exception as e:
            logging.warning(f"Could not fetch symbol for token {checksum_address}: {e}")
            symbol = cache_key

        self.token_metadata_cache[cache_key] = {
            "symbol": symbol,
            "address": cache_key,
        }

        save_token_metadata_cache(self.token_metadata_cache)

        return symbol

    def get_token_decimals(self, token_address):
        cache_key = token_address.lower()

        if cache_key in self.token_decimals_cache:
            return self.token_decimals_cache[cache_key]

        checksum_address = Web3.to_checksum_address(token_address)

        erc20_abi = [
            {
                "name": "decimals",
                "outputs": [{"type": "uint8"}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function",
            }
        ]

        token = self.web3_client.eth.contract(
            address=checksum_address,
            abi=erc20_abi,
        )

        try:
            decimals = token.functions.decimals().call()
        except Exception as e:
            logging.warning(f"Could not fetch decimals for token {checksum_address}: {e}")
            decimals = 18

        self.token_decimals_cache[cache_key] = decimals
        save_token_decimals_cache(self.token_decimals_cache)

        return decimals

    def fetch_transfers_by_block_from_cache(self, block_number):
        from receipt_cache import get_block_receipts
        payload = get_block_receipts(block_number)

        tx_transfers = {}

        for tx_hash, receipt in payload["receipts"].items():
            transfers = self.extract_transfers_from_receipt(receipt)

            if transfers:
                tx_transfers[tx_hash] = transfers

        return tx_transfers

    def fetch_block_transactions(self, block_number: Optional[int] = None) -> List[Transaction]:
        if block_number is None:
            block_number = 'latest'
        block = self.web3_client.eth.get_block(block_number, full_transactions=True)
        # return [Transaction(tx['hash'], tx['from'], tx['to']) for tx in block['transactions']]
        return [Transaction(
            tx_hash=tx["hash"],
            from_addr=tx["from"],
            to_addr=tx["to"] if tx["to"] else None,
            block_height=block["number"],
            timestamp=None,          # optional (not directly in eth_getBlock)
            gas_price=tx.get("gasPrice"),
            value=tx.get("value", 0),
        )   
    for tx in block["transactions"]
]
    
    def fetch_transaction_by_tx(self, tx_hash):
        return self.web3_client.eth.get_transaction(tx_hash)
    
    def fetch_local_transactions(self, block_number: Optional[int] = None) -> List[Transaction]:
        csv_path = Path(__file__).parent / "data" / "demo.csv"
        transactions: List[Transaction] = []

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:

                # ----------------------------
                # SAFE BLOCK HEIGHT HANDLING
                # ----------------------------
                block_height_raw = row.get("included_at_block_height")

                # skip malformed rows safely
                if block_number is not None:
                    if not block_height_raw:
                        continue
                    if int(block_height_raw) != block_number:
                        continue

                # ----------------------------
                # SAFE FIELD PARSING
                # ----------------------------
                transactions.append(
                    Transaction(
                        tx_hash=row["hash"],
                        from_addr=row["from"],
                        to_addr=row["to"] or None,

                        # MEV fields (safe casts)
                        block_height=int(block_height_raw) if block_height_raw else None,
                        timestamp=int(row["timestamp_ms"]) if row.get("timestamp_ms") else None,
                        gas_price=int(row["gas_price"]) if row.get("gas_price") else None,
                        value=int(row["value"]) if row.get("value") else 0,
                    )
                )

        return transactions
    
    def extract_transfers_from_receipt(self, receipt):
        transfers = []

        for log in receipt["logs"]:
            topics = log.get("topics", [])

            if len(topics) < 3:
                continue

            topic0 = topics[0]

            # Cached receipts store topics as strings.
            # Live Web3 receipts store topics as HexBytes.
            if not isinstance(topic0, str):
                topic0 = topic0.hex()

            if log["topics"] and topic0 == self.TRANSFER_TOPIC:
                data = log.get("data")
                if data in (None, "", "0x"):
                    continue

                if isinstance(data, str):
                    if not data.startswith("0x"):
                        data = "0x" + data

                    raw_value = Web3.to_int(hexstr=data)
                else:
                    raw_value = Web3.to_int(data)

                token_address = log["address"].lower()
                decimals = self.get_token_decimals(token_address)

                topic1 = topics[1]
                topic2 = topics[2]

                if not isinstance(topic1, str):
                    topic1 = topic1.hex()

                if not isinstance(topic2, str):
                    topic2 = topic2.hex()

                transfers.append({
                    "token": token_address,
                    "from": "0x" + topic1[-40:],
                    "to": "0x" + topic2[-40:],
                    "value": raw_value / (10 ** decimals),
                })

        return transfers
    
    def fetch_transfer_by_tx(self, tx_hash):
        try:
            receipt = self.web3_client.eth.get_transaction_receipt(tx_hash)
        except Exception as e:
            logging.exception(f"Error fetching {tx_hash}, Error: {e}")
            return []

        return self.extract_transfers_from_receipt(receipt)

    def fetch_range(self, start: int, end: int) -> List[Transaction]:
        pass
    def decode_swap_events(self, tx_receipt) -> List[SwapEvent]:
        pass
    def get_mempool_pending(self) -> List[Transaction]:
        pass

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch blockchain data by block or transaction")
    subparsers = parser.add_subparsers(dest="command", required=True)

    block_parser = subparsers.add_parser("block", help="Fetch by block number")
    block_parser.add_argument("id", type=int, help="Block number")

    tx_parser = subparsers.add_parser("tx", help="Fetch by transaction hash")
    tx_parser.add_argument("id", type=str, help="Transaction hash")

    frontrun_parser = subparsers.add_parser("frontrun", help="Detect MEV front-running")
    frontrun_parser.add_argument("id", type=int, help="Block number")

    api_frontrun_parser = subparsers.add_parser("api-frontrun")
    api_frontrun_parser.add_argument("id", type=int)

    sandwich_parser = subparsers.add_parser("sandwich", help="Detect sandwich attacks (API)")
    sandwich_parser.add_argument("id", type=int, help="Block number")

    return parser.parse_args()

def main() -> None:
    args = parse_args()
    client = BlockchainFetcher()

    if args.command == "tx":
        tx = client.fetch_transfer_by_tx(args.id)
        arbitrage_result = calculate_arbitrage(tx)
        print(arbitrage_result)

    elif args.command == "block":
        txs = client.fetch_block_transactions(args.id)
        print(txs)
    
    #for front running with the csv data
    elif args.command == "frontrun":
        txs = client.fetch_local_transactions(args.id)
        result = detect_front_running(txs)
        print(result)
    
    elif args.command == "api-frontrun":
        txs = client.fetch_block_transactions(args.id)
        result = detect_front_running(txs)
        print(result)
    
    elif args.command == "sandwich":
        txs = client.fetch_local_transactions(args.id)
        result = detect_sandwich_attacks(txs)
        print(result)
    
if __name__ == "__main__":
    main()
