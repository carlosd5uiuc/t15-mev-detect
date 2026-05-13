from matplotlib import pyplot as plt

labels = [
    "Ground Truth\nArbitrage Value",
    "Detected\nArbitrage Value"
]

values = [
    7295448.585416881,
    838458.0364063912
]

plt.figure()
plt.bar(labels, values)
plt.title("Arbitrage Detection Performance Comparison (USD)")
plt.ylabel("Value (USD)")
plt.show()