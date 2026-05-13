import pandas as pd

data = {
    "Metric": [
        "Total labeled arbitrage transactions",
        "Detected arbitrage transactions",
        "Detection rate"
    ],
    "Value": [
        250,
        250,
        1.0
    ]
}

df = pd.DataFrame(data)

print(df.to_latex(index=False))