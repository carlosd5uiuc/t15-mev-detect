from matplotlib import pyplot as plt

labels = [
    "Ground Truth Arbitrage Value (USD)",
    "Detected Arbitrage Value (USD)"
]

values = [
    7295448.585416881,
    838458.0364063912
]

plt.figure()
plt.plot(labels, values, marker='o')
plt.title("Arbitrage Detection Performance Comparison")
plt.ylabel("Value (USD)")
plt.xticks(rotation=25, ha='right')
plt.tight_layout()
plt.show()