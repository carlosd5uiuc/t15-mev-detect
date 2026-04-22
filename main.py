import argparse

from blockchain_fetcher import BlockchainFetcher
from mev_types.arbitrage import calculate_arbitrage

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch blockchain data by block or transaction")
    subparsers = parser.add_subparsers(dest="command", required=True)

    block_parser = subparsers.add_parser("block", help="Fetch by block number")
    block_parser.add_argument("id", type=int, help="Block number")

    block_parser.add_argument("start", type=int, help="Start tx index (inclusive)")
    block_parser.add_argument("end", type=int, help="End tx index (exclusive)")

    tx_parser = subparsers.add_parser("tx", help="Fetch by transaction hash")
    tx_parser.add_argument("id", type=str, help="Transaction hash")

    return parser.parse_args()

def main() -> None:
    args = parse_args()
    client = BlockchainFetcher()

    if args.command == "tx":
        transfers = client.fetch_transfer_by_tx(args.id)
        arbitrage_result = calculate_arbitrage(transfers)
        print(arbitrage_result)

    elif args.command == "block":
        txs = client.fetch_block_transactions(args.id)
        transfers = [client.fetch_transfer_by_tx(t.tx_hash) for t in txs[args.start:args.end]]
        for transfer in transfers:
            result = calculate_arbitrage(transfer)
            if len(result): print(result)
    
if __name__ == "__main__":
    main()
