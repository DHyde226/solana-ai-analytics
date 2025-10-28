# src/features.py
import pandas as pd
import json

def build_wallet_features(input_csv="global_transactions.csv",
                          output_csv="wallet_features.csv"):
    df = pd.read_csv(input_csv)
    wallet_stats = {}

    for _, row in df.iterrows():
        transfers = json.loads(row.get("transfers", "[]"))
        fee = row.get("fee", 0)

        for tr in transfers:
            src = tr.get("source")
            lamports = tr.get("lamports", 0)

            if not src:
                continue
            w = wallet_stats.setdefault(src, {"tx_count": 0,
                                              "total_sent": 0,
                                              "total_fee": 0})
            w["tx_count"] += 1
            w["total_sent"] += lamports
            w["total_fee"] += fee

    df_feat = pd.DataFrame.from_dict(wallet_stats, orient="index")
    df_feat["avg_fee"] = df_feat["total_fee"] / df_feat["tx_count"]
    df_feat.to_csv(output_csv)
    print(f"✅ Saved wallet-level features to {output_csv}")

if __name__ == "__main__":
    build_wallet_features()
