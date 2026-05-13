# MEV Detection Tool

## Data
Extracted from Flashbots' [Mempool Dumpster](https://mempool-dumpster.flashbots.net/index.html)

## API Key

This project requires an Infura API key to connect to the Ethereum network.

Create an Infura account and generate an API key at: [https://www.infura.io/](https://www.infura.io/)

Then add the key to your environment variables:

```env
RPC_URL_KEY=YOUR_API_KEY
```

Replace `YOUR_API_KEY` with your actual Infura API key.


## Running the Streamlit GUI

Activate the virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the GUI:

```bash
streamlit run gui.py
```

For arbitrage block analysis, receipt caching happens automatically.

```text
First run:
Fetching receipts for block <block_number> from API

Later runs:
Loaded receipts for block <block_number> from cache
```

Cached transaction receipt files are stored locally under:

```text
data/receipts/
```

The cache folder is created automatically when needed.
```
