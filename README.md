# MEV Detection Tool

## Data
Extracted from Flashbots' [Mempool Dumpster](https://mempool-dumpster.flashbots.net/index.html)

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
