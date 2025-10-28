# src/analyze_whales.py
import pandas as pd
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt

def detect_whales(input_csv="wallet_features.csv"):
    df = pd.read_csv(input_csv)
    X = df[["tx_count", "total_sent", "avg_fee"]].fillna(0)

    model = IsolationForest(contamination=0.05, random_state=42)
    df["anomaly"] = model.fit_predict(X)

    whales = df[df["anomaly"] == -1].sort_values("total_sent", ascending=False)
    whales.to_csv("whale_wallets.csv")
    print("🐋 Top detected whales:")
    print(whales.head(10))
    print("✅ Saved all detected whales to whale_wallets.csv")

    plt.scatter(df["tx_count"], df["total_sent"],
                c=(df["anomaly"] == -1), cmap="coolwarm", alpha=0.6)


    plt.xlabel("Transaction Count")
    plt.ylabel("Total SOL Sent (lamports)")
    plt.title("Whale / Anomaly Detection")
    plt.show()

if __name__ == "__main__":
    detect_whales()
