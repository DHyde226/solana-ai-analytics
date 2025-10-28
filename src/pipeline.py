# src/pipeline.py
import json
import pandas as pd
from datetime import datetime
from src.solscan_api import get_recent_transactions, get_transaction
from src.data_store import create_tables, insert_transactions, get_recent_transactions as get_recent_transactions_db


# ---------- Extraction helpers ----------
def _extract_fee(tx: dict) -> int:
    """Extract transaction fee from meta."""
    return (tx.get("meta") or {}).get("fee", 0)


def _infer_type(tx: dict) -> str:
    """Guess the transaction type from parsed instruction data (safe version)."""
    try:
        instrs = tx.get("transaction", {}).get("message", {}).get("instructions", [])
        for ix in instrs:
            # skip if instruction is not a dictionary
            if not isinstance(ix, dict):
                continue
            parsed = ix.get("parsed")
            if not isinstance(parsed, dict):
                continue
            prog = ix.get("program")
            t = parsed.get("type") or "unknown"
            return f"{prog}:{t}" if prog else t
    except Exception:
        pass
    return "unknown"



def _extract_transfers(tx: dict):
    """Extract SOL or SPL token transfers from parsed instructions (safe version)."""
    transfers = []

    try:
        instructions = tx.get("transaction", {}).get("message", {}).get("instructions", [])
    except Exception:
        return transfers

    for ix in instructions:
        # Skip if not a proper dict (some instructions are just strings)
        if not isinstance(ix, dict):
            continue

        parsed = ix.get("parsed")
        if not isinstance(parsed, dict):
            continue

        prog = ix.get("program")
        t = parsed.get("type")
        info = parsed.get("info", {})

        # --- SOL transfer ---
        if prog == "system" and t == "transfer":
            transfers.append({
                "kind": "sol",
                "source": info.get("source"),
                "destination": info.get("destination"),
                "lamports": info.get("lamports"),
            })

        # --- SPL token transfer ---
        elif prog == "spl-token" and t in ("transfer", "transferChecked"):
            amount = info.get("amount")
            if isinstance(info.get("tokenAmount"), dict):
                amount = info["tokenAmount"].get("amount")
            transfers.append({
                "kind": "spl-token",
                "mint": info.get("mint"),
                "source": info.get("source"),
                "destination": info.get("destination"),
                "amount": amount,
            })

    return transfers



# ---------- Normalization ----------
def normalize_transactions(wallet="global", limit=10):
    """Fetch recent transactions from DB and normalize them into a DataFrame."""
    rows = get_recent_transactions_db(wallet, limit=limit)
    tx_list = []

    for sig, block_time, raw_json in rows:
        try:
            tx = json.loads(raw_json)
        except json.JSONDecodeError:
            continue

        fee = _extract_fee(tx)
        ttype = _infer_type(tx)
        transfers = _extract_transfers(tx)

        normalized = {
            "signature": sig,
            "block_time": block_time,
            "datetime": datetime.fromtimestamp(block_time) if block_time else None,
            "type": ttype,
            "fee": fee,
            "transfers": json.dumps(transfers),
        }
        tx_list.append(normalized)

    df = pd.DataFrame(tx_list)
    return df.sort_values(by="block_time", ascending=False)


# ---------- Full pipeline ----------
def run_pipeline(wallet="global", fetch_limit=0, normalize_limit=10000, output_csv=None):
    """
    Full pipeline: fetch -> store -> normalize -> save CSV.
    Works with Helius (global feed).
    """
    print("🔹 Creating tables if missing...")
    create_tables()

    # Always fetch new global transactions
    print(f"🔹 Fetching {fetch_limit} recent global transactions (Helius)...")
    sigs = get_recent_transactions(limit=fetch_limit)

    full_txs = []
    for tx in sigs:
        sig = tx.get("signature")
        if not sig:
            continue
        detail = get_transaction(sig)
        if detail:
            detail["signature"] = sig
            full_txs.append(detail)

    print(f"🔹 Inserting {len(full_txs)} transactions into DB...")
    insert_transactions(wallet, full_txs)

    print(f"🔹 Normalizing the most recent {normalize_limit} transactions...")
    df = normalize_transactions(wallet, limit=normalize_limit)

    if output_csv is None:
        output_csv = f"{wallet}_transactions.csv"

    df.to_csv(output_csv, index=False)
    print(f"✅ Pipeline complete. Normalized data saved to {output_csv}")


if __name__ == "__main__":
    run_pipeline("global")
