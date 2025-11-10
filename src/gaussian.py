# src/gaussian.py

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture
import matplotlib.pyplot as plt
import numpy as np

def run_gmm_clustering(input_csv="wallet_behavior_features.csv",
                       output_csv="wallet_clusters_gmm.csv"):
    """Cluster wallets using Gaussian Mixture Model (unsupervised soft clustering)."""

    print(f"📥 Loading wallet behavior features from: {input_csv}")
    df = pd.read_csv(input_csv)

    # --- Select numeric features only ---
    X = df.select_dtypes(include=["number"]).fillna(0)

    print(f"🧮 Using {X.shape[1]} numeric features for clustering ({X.shape[0]} wallets)")

    # --- Normalize data ---
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # --- Dimensionality reduction ---
    print("📉 Applying PCA (20 components)...")
    pca = PCA(n_components=20, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    print(f"✅ PCA reduced dimensionality from {X.shape[1]} → {X_pca.shape[1]}")

    # --- Evaluate optimal number of clusters using BIC ---
    bics = []
    n_values = range(3, 8)
    for n in n_values:
        gmm = GaussianMixture(n_components=n, covariance_type="diag", random_state=42)
        gmm.fit(X_pca)
        bics.append(gmm.bic(X_pca))
        print(f"BIC for {n} clusters: {bics[-1]:.2f}")

    best_n = n_values[np.argmin(bics)]
    print(f"\n🏆 Best number of clusters by BIC: {best_n}")

    # --- Fit final model ---
    print("🤖 Fitting final Gaussian Mixture Model...")
    gmm = GaussianMixture(n_components=best_n, covariance_type="diag", random_state=42)
    df["cluster"] = gmm.fit_predict(X_pca)

    # --- Visualize in 2D (first two PCA components) ---
    plt.figure(figsize=(8, 6))
    plt.scatter(X_pca[:, 0], X_pca[:, 1], c=df["cluster"], cmap="tab10", alpha=0.7)
    plt.xlabel("PCA 1")
    plt.ylabel("PCA 2")
    plt.title("Wallet Clusters (Gaussian Mixture Model)")
    plt.tight_layout()
    plt.show()

    # --- Cluster summaries ---
    print("\n📊 Cluster summary (mean values per cluster):")
    cluster_summary = df.groupby("cluster")[df.select_dtypes("number").columns].mean().round(3)

    print(cluster_summary.head())

    # --- Save results ---
    df.to_csv(output_csv, index=False)
    print(f"\n💾 Saved clustered wallet data to: {output_csv}")

    return df, cluster_summary


if __name__ == "__main__":
    run_gmm_clustering()
