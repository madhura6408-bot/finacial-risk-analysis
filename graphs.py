import matplotlib.pyplot as plt
import pandas as pd
df = pd.read_csv("transaction.csv", sep="|", quotechar='"', engine="python")
# Graph 1: Transaction Types
plt.figure(figsize=(8, 5))
df["Transaction_Type"].value_counts().plot(kind="bar")
plt.title("Transaction Types")
plt.xlabel("Transaction Type")
plt.ylabel("Number of Transactions")
plt.tight_layout()
plt.savefig("transaction_types.png")
plt.close()

# Graph 2: Transaction Channels
plt.figure(figsize=(8, 5))
df["channel"].value_counts().plot(kind="bar")
plt.title("Transaction Channels")
plt.xlabel("Channel")
plt.ylabel("Number of Transactions")
plt.tight_layout()
plt.savefig("transaction_channels.png")
plt.close()

# Graph 3: Transaction Amount Distribution
plt.figure(figsize=(8, 5))
df["amount"].dropna().plot(kind="hist", bins=10, edgecolor="black")
plt.title("Transaction Amount Distribution")
plt.xlabel("Transaction Amount")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig("transaction_amounts.png")
plt.close()

# Graph 4: Transactions by Region

plt.figure(figsize=(8, 5))

df["region"].value_counts().plot(kind="bar")

plt.title("Transactions by Region")
plt.xlabel("Region")
plt.ylabel("Number of Transactions")

plt.tight_layout()
plt.savefig("transactions_by_region.png")
plt.close()

print("All 4 graphs saved successfully.")