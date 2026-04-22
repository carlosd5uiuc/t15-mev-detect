import argparse

from blockchain_fetcher import BlockchainFetcher
from mev_types.arbitrage import calculate_arbitrage

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
        transfers = client.fetch_transfer_by_tx(args.id)
        arbitrage_result = calculate_arbitrage(transfers)
        print(arbitrage_result)

    elif args.command == "block":
        txs = client.fetch_block_transactions(args.id)
        # print(len(txs))
        # return
        # print(txs)
        idx = next((i for i, tx in enumerate(txs) if tx.tx_hash == '0xd5b0c82326493690e05c3ac4be63e8bb7763f1a99fbea6db293ec317c8ce5595'), -1)
        # print(idx)
        # print([t.tx_hash for t in txs[:10]])
        # for t in txs:
        #     print(t.tx_hash)
        transfers = [client.fetch_transfer_by_tx(t.tx_hash) for t in txs[:40]]
        # # print(transfers)
        for transfer in transfers:
            result = calculate_arbitrage(transfer)
            print(result)
    
if __name__ == "__main__":
    main()
