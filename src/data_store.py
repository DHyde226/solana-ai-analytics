import sqlite3
import json

DB_FILE = "wallets.db"

def connect_db():
    """Connect to SQLite database (or create if it doesn't exist)."""
    conn = sqlite3.connect(DB_FILE)
    return conn

def create_tables():
    """Create tables for storing wallet transactions."""
    conn = connect_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            wallet TEXT,
            signature TEXT PRIMARY KEY,
            block_time INTEGER,
            raw_json TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_transactions(wallet, transactions):
    """Insert a list of transactions into the database."""
    conn = connect_db()
    c = conn.cursor()
    for tx in transactions:
        signature = tx.get('signature') or tx.get('txHash')  # RPC vs REST
        block_time = tx.get('blockTime', 0)
        raw_json = json.dumps(tx)
        try:
            c.execute(
                "INSERT OR IGNORE INTO transactions (wallet, signature, block_time, raw_json) VALUES (?, ?, ?, ?)",
                (wallet, signature, block_time, raw_json)
            )
        except sqlite3.Error as e:
            print(f"[DB ERROR] {e}")
    conn.commit()
    conn.close()

def get_recent_transactions(wallet, limit=5):
    """Fetch the most recent transactions for a wallet."""
    conn = connect_db()
    c = conn.cursor()
    c.execute(
        "SELECT signature, block_time, raw_json FROM transactions WHERE wallet=? ORDER BY block_time DESC LIMIT ?",
        (wallet, limit)
    )
    rows = c.fetchall()
    conn.close()
    return rows

