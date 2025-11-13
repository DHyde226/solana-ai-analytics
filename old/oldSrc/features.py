# src/features.py
import pandas as pd
import json
from collections import defaultdict

def build_wallet_features(input_csv="global_transactions.csv",
                          output_csv="wallet_features.csv"):
    """
    Build per-wallet aggregated features from normalized transaction data.
    Includes SOL + SPL transfers, minting, token diversity, and DeFi activity.
    """

    df = pd.read_csv(input_csv)
    wallet_stats = {}

    for _, row in df.iterrows():
        # --- Safely parse transfers and type ---
        raw = row.get("transfers", "[]")
        try:
            transfers = json.loads(raw if isinstance(raw, str) else "[]")
        except json.JSONDecodeError:
            transfers = []

        fee = row.get("fee", 0) or 0
        tx_type = row.get("type", "unknown") or "unknown"

        for tr in transfers:
            if not isinstance(tr, dict):
                continue

            src = tr.get("source")
            dst = tr.get("destination")
            kind = tr.get("kind", "")
            mint = tr.get("mint")
            lamports = int(tr.get("lamports", 0) or 0)
            amount = tr.get("amount")
            if isinstance(amount, str) and amount.isdigit():
                amount = int(amount)
            elif not isinstance(amount, (int, float)):
                amount = 0

            # ---- Initialize wallet entry ----
            wallet = src or dst
            if not wallet:
                continue

            w = wallet_stats.setdefault(wallet, {
                "tx_count": 0,
                "total_fee": 0,
                "total_sent_sol": 0,
                "spl_tokens_sent": defaultdict(int),  # mint -> amount
                "mint_count": 0,
                "tokens_minted": 0,
                "activity_types": set()
            })

            # ---- Generic accounting ----
            w["tx_count"] += 1
            w["total_fee"] += int(fee)
            w["activity_types"].add(tx_type)

            # ---- SOL transfers ----
            if kind == "sol" and src:
                w["total_sent_sol"] += lamports

            # ---- SPL transfers ----
            elif kind == "spl-token" and src and mint:
                w["spl_tokens_sent"][mint] += int(amount)

            # ---- SPL minting (mintTo or initializeMint) ----
            elif kind == "spl-token" and tr.get("type") in ("mintTo", "initializeMint"):
                w["mint_count"] += 1
                w["tokens_minted"] += int(amount)

    # ---------- Flatten and compute derived features ----------
    flattened = []
    for wallet, data in wallet_stats.items():
        spl_summary = ", ".join([f"{mint[:6]}...:{amt}" for mint, amt in data["spl_tokens_sent"].items()])
        token_diversity = len(data["spl_tokens_sent"])
        defi_activity_count = len(data["activity_types"])
        avg_fee = data["total_fee"] / data["tx_count"] if data["tx_count"] else 0

        flattened.append({
            "wallet": wallet,
            "tx_count": data["tx_count"],
            "total_fee": data["total_fee"],
            "avg_fee": avg_fee,
            "total_sent_sol": data["total_sent_sol"],
            "token_diversity": token_diversity,
            "defi_activity_count": defi_activity_count,
            "mint_count": data["mint_count"],
            "tokens_minted": data["tokens_minted"],
            "spl_tokens_sent": spl_summary
        })

    df_feat = pd.DataFrame(flattened)
    df_feat.to_csv(output_csv, index=False)
    print(f"✅ Saved wallet-level features (SOL + SPL + DeFi) to {output_csv}")


if __name__ == "__main__":
    build_wallet_features()
