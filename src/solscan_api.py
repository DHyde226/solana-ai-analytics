# src/solscan_api.py
import requests
import json
import time
from src.data_store import create_tables, insert_transactions, get_recent_transactions as get_recent_transactions_db

# --- Helius setup ---
HELIUS_API_KEY = "868e22fc-d691-43bc-a426-f720bae3cae3"
RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

SYSTEM_PROGRAM = "11111111111111111111111111111111"


def get_recent_transactions(limit=10, before=None):
    """Fetch recent transactions for the Solana mainnet using Helius RPC.
    Optionally use 'before' to paginate backwards."""
    headers = {"Content-Type": "application/json"}
    params = {"limit": limit}
    if before:
        params["before"] = before  # paginate older signatures

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [SYSTEM_PROGRAM, params],
    }

    try:
        response = requests.post(RPC_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json().get("result", [])
        return result
    except requests.RequestException as e:
        print(f"[Helius ERROR] {e}")
        return []


def get_transaction(signature):
    """Fetch full transaction details by signature."""
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [signature, {"encoding": "jsonParsed"}],
    }

    try:
        response = requests.post(RPC_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json().get("result", {})
    except requests.RequestException as e:
        print(f"[Helius ERROR] {e}")
        return None


if __name__ == "__main__":
    print("🔍 Fetching recent global Solana transactions (via Helius)...")

    create_tables()
    all_txs = []
    before_sig = None  # for pagination
    total_to_fetch = 10000  # target dataset size
    batch_size = 50
    fetched = 0

    while fetched < total_to_fetch:
        print(f"\n📦 Fetching batch {fetched // batch_size + 1} (up to {batch_size} txs)...")
        sigs = get_recent_transactions(limit=batch_size, before=before_sig)
        if not sigs:
            print("No more results or API error — stopping.")
            break

        full_txs = []
        for tx in sigs:
            sig = tx.get("signature")
            if not sig:
                continue
            detail = get_transaction(sig)
            if detail:
                detail["signature"] = sig
                full_txs.append(detail)

        insert_transactions("global", full_txs)
        all_txs.extend(full_txs)
        fetched += len(full_txs)

        # Set next pagination cursor (oldest signature in the batch)
        before_sig = sigs[-1]["signature"]
        print(f"✅ Inserted {len(full_txs)} new transactions (total so far: {fetched})")

        # Avoid hitting rate limits
        time.sleep(2)

    print(f"\n🎉 Done! Total transactions fetched: {fetched}")
    print("💾 Last stored transactions from DB:")
    stored = get_recent_transactions_db("global", limit=5)
    for s in stored:
        print(f"- {s[0]} at {s[1]}")



