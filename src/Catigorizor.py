import pandas as pd
import numpy as np

# --------------------------------------------------
# 1️⃣ TYPE → CATEGORY MAPPING
# --------------------------------------------------
TYPE_CATEGORY_MAP = {
    # Retail / normal
    "system:transfer": "retail",

    # Bot / automation
    "system:advanceNonce": "bot",
    "address-lookup-table:createLookupTable": "bot",
    "address-lookup-table:extendLookupTable": "bot",

    # System / infrastructure
    "system:createAccount": "system",
    "system:createAccountWithSeed": "system",
    "spl-associated-token-account:create": "system",
    "spl-associated-token-account:createIdempotent": "system",
    "spl-token:closeAccount": "system",

    # DeFi / fungible operations
    "spl-token:transfer": "defi",
    "spl-token:transferChecked": "defi",
    "spl-token:mintTo": "defi",
    "spl-token:burn": "defi",
    "spl-token:approve": "defi",
    "spl-token:approveChecked": "defi",

    # Unknown
    "unknown": "unclassified",
}


# --------------------------------------------------
# 2️⃣ BUILD CATEGORY RATIOS FROM TYPE COUNTS
# --------------------------------------------------
def compute_category_ratios(df):
    """Compute aggregate ratios (defi, bot, system, retail) from per-type count columns."""
    df["defi_ratio"] = 0.0
    df["bot_ratio"] = 0.0
    df["system_ratio"] = 0.0
    df["retail_ratio"] = 0.0

    type_cols = [c for c in df.columns if c.startswith("type_")]
    if not type_cols:
        print("⚠️ No type_* columns found — skipping ratio computation.")
        return df

    for col in type_cols:
        type_name = col.replace("type_", "").replace("_", ":")
        category = TYPE_CATEGORY_MAP.get(type_name, "unclassified")
        ratio = df[col] / df["tx_count"].replace(0, np.nan)

        if category == "defi":
            df["defi_ratio"] += ratio
        elif category == "bot":
            df["bot_ratio"] += ratio
        elif category == "system":
            df["system_ratio"] += ratio
        elif category == "retail":
            df["retail_ratio"] += ratio

    df.fillna(0, inplace=True)
    return df


# --------------------------------------------------
# 3️⃣ CLASSIFICATION LOGIC
# --------------------------------------------------
def classify_wallet(row):
    """Assign wallet to archetype using rule-based logic."""
    tx_count = row.get("tx_count", 0)
    total_sent = row.get("total_sent_sol", 0)
    avg_value = row.get("avg_tx_value", 0)
    avg_interval = row.get("avg_tx_interval", np.inf)
    dest_entropy = row.get("dest_entropy", 0)
    token_div = row.get("token_diversity", 0)
    fee_ratio = row.get("fee_ratio", 0)
    defi_ratio = row.get("defi_ratio", 0)
    bot_ratio = row.get("bot_ratio", 0)
    system_ratio = row.get("system_ratio", 0)
    retail_ratio = row.get("retail_ratio", 0)

    # --- Dormant wallet ---
    if tx_count <= 3 and total_sent < 0.1:
        return "Dormant Wallet"

    # --- Whale / Institutional ---
    if total_sent > 100 or avg_value > 10:
        if tx_count < 100 and avg_interval > 10000:
            return "Whale / Institutional Wallet"

    # --- Bot / Arbitrage ---
    if tx_count > 300 and avg_interval < 30 and bot_ratio > 0.5 and dest_entropy < 0.3:
        return "Bot / Arbitrage Wallet"

    # --- Hybrid DeFi Bot ---
    if tx_count > 200 and defi_ratio > 0.3 and bot_ratio > 0.3:
        return "Hybrid DeFi Bot"

    # --- DeFi Trader / Yield Farmer ---
    if defi_ratio > 0.5 and token_div >= 10:
        return "DeFi Trader / Yield Farmer"

    # --- System / Infrastructure ---
    if system_ratio > 0.7 or (tx_count < 50 and dest_entropy < 0.2 and token_div < 3):
        return "System / Infrastructure Account"

    # --- Retail / Normal User ---
    if tx_count < 50 and defi_ratio < 0.2 and retail_ratio > 0.6:
        return "Retail Wallet"

    # Default catch-all
    return "Unclassified"


# --------------------------------------------------
# 4️⃣ PIPELINE
# --------------------------------------------------
def classify_wallets(input_csv="wallet_behavior_features.csv", output_csv="wallet_archetypes.csv"):
    df = pd.read_csv(input_csv)
    print(f"📥 Loaded {len(df)} wallets from {input_csv}")

    # Compute ratios
    df = compute_category_ratios(df)

    # Apply classification
    df["archetype"] = df.apply(classify_wallet, axis=1)

    # Save
    df.to_csv(output_csv, index=False)
    print(f"✅ Saved labeled archetypes to {output_csv}")

    # Summary
    print("\n📊 Archetype Counts:")
    print(df["archetype"].value_counts())

    return df


# --------------------------------------------------
# 5️⃣ RUN
# --------------------------------------------------
if __name__ == "__main__":
    classify_wallets("wallet_behavior_features.csv", "wallet_archetypes.csv")
