# 🪙 Solana Wallet Behavior Clustering & Anomaly Detection

This project performs **unsupervised clustering** and **anomaly detection** on Solana wallets using behavioral data.  
It extracts structured wallet-level features from raw Solana transaction data, applies **PCA** for dimensionality reduction, and uses a **Gaussian Mixture Model (GMM)** for clustering.  
Additionally, it performs **anomaly detection** to identify wallets exhibiting whale-like or abnormal transaction activity.

---

## 📁 Project Structure

```
solana-ai-analytics/
├── src/
│   ├── data_store.py            # SQLite3 helper functions for pipeline + Solscan API integration
│   ├── solscan_api.py           # Fetches transaction data from the Solscan API
│   ├── analyze_whales.py        # Detects whales and large transaction anomalies
│   ├── pipeline.py              # Normalizes database data and creates raw CSV output
│   ├── behavior_features.py     # Builds wallet_behavior_features.csv from raw transactions
│   ├── gaussian.py              # Runs PCA + GMM clustering for behavioral segmentation
│   ├── utils/                   # Optional helper utilities
│
├── old/                         # Legacy code and previous iterations
├── global_transactions.csv      # Raw Solana transaction data (input)
├── wallet_behavior_features.csv # Engineered wallet-level features (intermediate)
├── wallet_clusters_gmm.csv      # Final clustered dataset (output)
├── venv/                        # Python environment
└── README.md
```

---

## ⚙️ Workflow Overview

### 1️⃣ Collect Data from Solscan API

Run:
```bash
python -m src.solscan_api
```

This script:
- Connects to the Solscan API to collect wallet transaction data.
- Stores transaction metadata, transfers, and types in an SQLite3 database.

---

### 2️⃣ Normalize Data and Create Raw CSV

Run:
```bash
python -m src.pipeline
```

This script:
- Reads data from the SQLite database.
- Normalizes and flattens transaction records.
- Produces a unified CSV file: `global_transactions.csv`.

---

### 3️⃣ Extract Wallet Features

Run:
```bash
python -m src.behavior_features
```

This script:
- Aggregates transactions per wallet.
- Computes key metrics:
  - Transaction count
  - Total SOL sent
  - Average and total fees
  - Token diversity
  - Minting and DeFi activity ratios  
- Output: `wallet_behavior_features.csv`

---

### 4️⃣ Anomaly Detection (Whale Analysis)

Run:
```bash
python -m src.analyze_whales
```

This script:
- Uses **Isolation Forest** or similar algorithms to detect wallets with abnormal transaction volume or total SOL transfer.
- Flags likely **whales** or **bot-driven wallets**.
- Output: visualization of whale detection and filtered wallet data.

Example visualization:

```python
plt.scatter(df["tx_count"], df["total_sent_sol"],
            c=df["is_whale"], cmap="coolwarm", alpha=0.6)
plt.xlabel("Transaction Count")
plt.ylabel("Total SOL Sent (lamports)")
plt.title("Whale / Anomaly Detection")
plt.show()
```

---

### 5️⃣ Cluster Wallets via Gaussian Mixture Model (GMM)

Run:
```bash
python -m src.gaussian
```

This script:
1. Loads engineered wallet features.
2. Applies **StandardScaler** for normalization.
3. Reduces dimensionality using **PCA (20 components)**.
4. Fits a **Gaussian Mixture Model**.
   - Automatically determines optimal number of clusters (3–7) using **BIC**.
5. Assigns each wallet to a cluster.
6. Visualizes results in PCA and feature-based 2D plots.
7. Output: `wallet_clusters_gmm.csv`.

Example visualization:

```python
plt.figure(figsize=(8, 6))
for cluster_id in sorted(df["cluster"].unique()):
    mask = df["cluster"] == cluster_id
    plt.scatter(df.loc[mask, "tx_count"],
                df.loc[mask, "total_sent_sol"],
                label=f"Cluster {cluster_id}",
                alpha=0.7)
plt.xlabel("Transaction Count")
plt.ylabel("Total SOL Sent (lamports)")
plt.title("Wallet Clusters (Gaussian Mixture Model)")
plt.legend(title="Clusters", loc="best", fontsize=9)
plt.tight_layout()
plt.show()
```

---

## 🧭 Interpreting the Results

### Behavioral Archetypes by Cluster

| Cluster | Archetype | Description |
|----------|------------|-------------|
| **0** | 💤 Dormant Wallets | Claimed airdrops or made only one transaction |
| **1** | 💸 Light Users | Occasional swaps or small-value transfers |
| **2** | 🧱 Empty Wallets | Failed or incomplete transactions |
| **3** | 🐋 Mega Whales | Large-scale transactions (likely exchanges or institutions) |
| **4** | ⚙️ DeFi Users | Active token account creators and DEX participants |
| **5** | 🪙 Retail Whales | Mid-volume traders or smaller high-value users |
| **6** | 🤖 Bots / Validators | High-frequency automated accounts or programmatic senders |

---

## 📊 Visualization

### Whale Detection
- **X-axis:** Transaction count  
- **Y-axis:** Total SOL sent  
- **Color:** Red = Whale, Blue = Normal wallet  

### GMM Clustering
The PCA plot summarizes wallet activity across two axes:
- **PCA 1** — Overall activity level (volume & frequency)
- **PCA 2** — Token diversity and DeFi behavior

```python
plt.figure(figsize=(8, 6))
scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1],
                      c=df["cluster"], cmap="tab10", alpha=0.7)
handles, labels = scatter.legend_elements()
plt.legend(handles, labels, title="Clusters")
plt.xlabel("PCA 1")
plt.ylabel("PCA 2")
plt.title("Wallet Clusters (Gaussian Mixture Model)")
plt.show()
```

---

## 📈 Outputs

| File | Description |
|------|--------------|
| `global_transactions.csv` | Raw normalized transaction data |
| `wallet_behavior_features.csv` | Engineered wallet-level numeric features |
| `wallet_clusters_gmm.csv` | Clustered results with PCA-reduced features |
| `wallet_clusters_plot.png` | 2D PCA cluster visualization |
| `wallet_clusters_plot_sol.png` | 2D cluster visualization |
| `whale_detection_plot.png` | Whale and anomaly detection visualization |

---

## 🧠 Tech Stack

- **Python 3.10+**
- Libraries:
  - `pandas`, `numpy`
  - `scikit-learn` (PCA, GaussianMixture, IsolationForest)
  - `matplotlib`
  - `scipy`, `sqlite3`
- **Machine Learning**:
  - Dimensionality reduction: **PCA**
  - Clustering: **Gaussian Mixture Model**
  - Anomaly detection: **Isolation Forest**

---

## 🚀 Next Steps

- Add **t-SNE / UMAP** for richer embeddings  
- Incorporate **temporal analysis** (wallet evolution over time)  
- Enrich data with **on-chain metadata** (exchange, bot, validator tags)  
- Build a **behavioral similarity search** or scoring system for new wallets  

---

## 🧾 License

**MIT License © 2025 Daniel Vuksan**

---