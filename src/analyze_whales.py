# src/analyze_whales.py
import pandas as pd
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt

def detect_whales(input_csv="wallet_behavior_features.csv"):
    df = pd.read_csv(input_csv)
    X = df[["tx_count", "total_sent_sol", "avg_fee"]].fillna(0)

   # Choose top 5% of wallets by total_sent_sol as whales
    threshold = df["total_sent_sol"].quantile(0.99)
    df["is_whale"] = (df["total_sent_sol"] >= threshold).astype(int)

    whales = df[df["is_whale"] == 1].sort_values("total_sent_sol", ascending=False)

    whales.to_csv("whale_wallets.csv")
    print("🐋 Top detected whales:")
    print(whales.head(10))
    print("✅ Saved all detected whales to whale_wallets.csv")

    plt.scatter(df["tx_count"], df["total_sent_sol"],
            c=df["is_whale"], cmap="coolwarm", alpha=0.6)


    plt.xlabel("Transaction Count")
    plt.ylabel("Total SOL Sent (lamports)")
    plt.title("Whale / Anomaly Detection")
    plt.show()

if __name__ == "__main__":
    detect_whales()
