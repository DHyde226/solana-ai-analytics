import pandas as pd
import numpy as np
import json
from datetime import datetime
from collections import defaultdict
from scipy.stats import entropy


def load_transactions(input_csv="global_transactions.csv"):
    """Load and clean raw transaction data."""
    df = pd.read_csv(input_csv)
    print(f"📥 Loaded {len(df)} transactions")
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    return df


def calc_entropy(items):
    """Helper to compute normalized entropy of a list (diversity measure)."""
    if not items:
        return 0
    values, counts = np.unique(items, return_counts=True)
    probs = counts / counts.sum()
    return float(entropy(probs))


def extract_wallet_features(df):
    """
    Aggregate raw transactions into per-wallet feature vectors.
    Adds count features for each transaction type (how many times each type occurs).
    """
    wallet_stats = defaultdict(lambda: {
        "timestamps": [],
        "destinations": [],
        "lamports_sent": [],
        "fees": [],
        "tokens": [],
        "mint_events": 0,
        "defi_programs": set(),
        "type_counts": defaultdict(int),  # store counts per type
    })

    DEFI_PROGRAMS = [
        "Raydium", "Jupiter", "Orca", "Meteora", "Marginfi",
        "Lifinity", "Saber", "Marinade", "Kamino", "Drift"
    ]

    all_types = set()  # track all types globally for consistent columns

    for _, row in df.iterrows():
        try:
            transfers = json.loads(row.get("transfers", "[]"))
        except Exception:
            continue

        fee = row.get("fee", 0)
        t = None
        if "datetime" in row and pd.notna(row["datetime"]):
            try:
                t = pd.to_datetime(row["datetime"])
            except Exception:
                t = None

        tx_type = row.get("type", "unknown")
        all_types.add(tx_type)

        for tr in transfers:
            src = tr.get("source")
            dst = tr.get("destination")
            lamports = tr.get("lamports", 0)
            kind = tr.get("kind", "")
            mint = tr.get("mint", "")

            if not src:
                continue

            w = wallet_stats[src]
            w["timestamps"].append(t)
            w["fees"].append(fee)
            w["destinations"].append(dst)
            w["lamports_sent"].append(lamports)

            # increment count for this type
            w["type_counts"][tx_type] += 1

            if kind == "spl-token":
                w["tokens"].append(mint)
                if "mint" in str(mint).lower() or lamports == 0:
                    w["mint_events"] += 1

            if dst and any(p.lower() in str(dst).lower() for p in DEFI_PROGRAMS):
                w["defi_programs"].add(dst)

    data = []
    for wallet, s in wallet_stats.items():
        timestamps = sorted([t for t in s["timestamps"] if isinstance(t, datetime)])
        tx_count = len(timestamps)
        if tx_count == 0:
            continue

        if len(timestamps) > 1:
            diffs = np.diff([t.timestamp() for t in timestamps])
            avg_interval = np.mean(diffs)
            std_interval = np.std(diffs)
        else:
            avg_interval = std_interval = 0

        lamports = np.array(s["lamports_sent"]) if s["lamports_sent"] else np.array([0])
        total_sent_sol = lamports.sum() / 1e9
        avg_tx_value = lamports.mean() / 1e9
        median_tx_value = np.median(lamports) / 1e9
        max_tx_value = lamports.max() / 1e9
        total_fee = np.sum(s["fees"])
        avg_fee = np.mean(s["fees"]) if s["fees"] else 0

        dest_entropy = calc_entropy([d for d in s["destinations"] if d])
        token_diversity = len(set(s["tokens"]))
        unique_destinations = len(set([d for d in s["destinations"] if d]))

        mint_ratio = s["mint_events"] / tx_count
        fee_ratio = total_fee / tx_count if tx_count else 0

        record = {
            "wallet": wallet,
            "tx_count": tx_count,
            "total_sent_sol": total_sent_sol,
            "avg_tx_value": avg_tx_value,
            "median_tx_value": median_tx_value,
            "max_tx_value": max_tx_value,
            "avg_fee": avg_fee,
            "total_fee": total_fee,
            "fee_ratio": fee_ratio,
            "avg_tx_interval": avg_interval,
            "std_tx_interval": std_interval,
            "unique_destinations": unique_destinations,
            "dest_entropy": dest_entropy,
            "token_diversity": token_diversity,
            "mint_count": s["mint_events"],
            "mint_ratio": mint_ratio,
        }

        # add type counts (integer)
        for tx_type in all_types:
            col_name = f"type_{tx_type.replace(':', '_')}"
            record[col_name] = s["type_counts"].get(tx_type, 0)

        data.append(record)

    df_feat = pd.DataFrame(data)
    print(f"✅ Extracted {len(df_feat)} wallets with per-type counts.")
    return df_feat


def build_behavior_features(input_csv="global_transactions.csv",
                            output_csv="wallet_behavior_features.csv"):
    df = load_transactions(input_csv)
    df_feat = extract_wallet_features(df)
    df_feat.to_csv(output_csv, index=False)
    print(f"💾 Saved wallet features with type counts to {output_csv}")


if __name__ == "__main__":
    build_behavior_features()
