import argparse
import os
import logging
import csv
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from web3 import Web3

logging.basicConfig(level=logging.INFO)
from arbitrage import calculate_arbitrage

load_dotenv()
rpc_url_key = os.getenv("RPC_URL_KEY")

class Transaction:
    def __init__(self, tx_hash, from_addr, to_addr, **kwargs):
        self.tx_hash = tx_hash if isinstance(tx_hash, str) else tx_hash.hex()
        self.to_addr = to_addr
        self.from_addr = from_addr

    def __repr__(self):
        return f"Tx({self.tx_hash}, from={self.from_addr}, to={self.to_addr})"

class SwapEvent:
    pass

class BlockchainFetcher:
    def __init__(self):
        self.web3_client = Web3(Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{rpc_url_key}"))
        self.web3_client.is_connected()
        self.TRANSFER_TOPIC = self.web3_client.keccak(text="Transfer(address,address,uint256)").hex()

    def fetch_block_transactions(self, block_number: Optional[int] = None) -> List[Transaction]:
        if block_number is None:
            block_number = 'latest'
        block = self.web3_client.eth.get_block(block_number, full_transactions=True)
        return [Transaction(tx['hash'], tx['from'], tx['to']) for tx in block['transactions']]
    
    def fetch_transaction_by_tx(self, tx_hash):
        return self.web3_client.eth.get_transaction(tx_hash)
    
    def fetch_local_transactions(self, block_number: Optional[int] = None) -> List[Transaction]:
        csv_path = Path(__file__).with_name("2026-03-01-100k.csv")
        transactions: List[Transaction] = []

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                if block_number is not None and int(row["included_at_block_height"]) != block_number:
                    continue

                transactions.append(
                    Transaction(
                        row["hash"],
                        row["from"],
                        row["to"] or None,
                    )
                )

        return transactions
    
    def fetch_transfer_by_tx(self, tx_hash):
        try:
            receipt = self.web3_client.eth.get_transaction_receipt(tx_hash)
        except Exception as e:
            logging.exception(f"Error fetching {tx_hash}, Error: {e}")
            return

        transfers = []
        for log in receipt["logs"]:
            if log["topics"][0].hex() == self.TRANSFER_TOPIC:
                erc20_abi = [
                                {
                                    "name": "decimals",
                                    "outputs": [{"type": "uint8"}],
                                    "inputs": [],
                                    "stateMutability": "view",
                                    "type": "function",
                                }
                            ]
                raw_value = Web3.to_int(log["data"])
                token = self.web3_client.eth.contract(address=log["address"], abi=erc20_abi)
                decimals = token.functions.decimals().call()

                transfers.append({
                    "token": log["address"],
                    "from": "0x" + log["topics"][1].hex()[-40:],
                    "to": "0x" + log["topics"][2].hex()[-40:],
                    "value": raw_value / (10 ** decimals)
                })
        return transfers

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
    
if __name__ == "__main__":
    main()
