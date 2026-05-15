import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

# Load combined features
X = np.load("data/processed/combined_call_features.npy")
sources = np.load("data/processed/combined_call_sources.npy", allow_pickle=True)
print(f"Loaded {len(X)} call features")

# Normalize
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# PCA
print("Running PCA...")
pca = PCA(n_components=50, random_state=42)
X_reduced = pca.fit_transform(X_scaled)
print(f"Explained variance: {sum(pca.explained_variance_ratio_):.2%}")

# Find optimal k
print("Finding optimal clusters...")
silhouette_scores = []
K_range = range(2, 15)
for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_reduced)
    score = silhouette_score(X_reduced, labels)
    silhouette_scores.append(score)
    print(f"  k={k}: silhouette score = {score:.3f}")

best_k = K_range[np.argmax(silhouette_scores)]
print(f"\nBest k: {best_k}")

# Final clustering
kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
clusters = kmeans.fit_predict(X_reduced)
unique, counts = np.unique(clusters, return_counts=True)

# Cluster composition by source
print("\nCluster composition by source:")
for i in unique:
    mask = clusters == i
    cluster_sources = sources[mask]
    orcasound_count = np.sum(cluster_sources == 'orcasound')
    watkins_count = np.sum(cluster_sources == 'watkins')
    print(f"  Cluster {i}: {counts[i]} calls | {orcasound_count} orcasound | {watkins_count} watkins")

# Visualize
pca_2d = PCA(n_components=2, random_state=42)
X_2d = pca_2d.fit_transform(X_scaled)

plt.figure(figsize=(14, 5))

plt.subplot(1, 2, 1)
scatter = plt.scatter(X_2d[:, 0], X_2d[:, 1], c=clusters, cmap='tab10', alpha=0.6, s=20)
plt.colorbar(scatter)
plt.title(f"Orca Call Clusters (k={best_k})")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")

plt.subplot(1, 2, 2)
plt.bar([f"Cluster {i}" for i in unique], counts, color='steelblue')
plt.title("Calls per Cluster")
plt.ylabel("Number of Calls")
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig("data/processed/call_clusters.png")
plt.show()

np.save("data/processed/call_cluster_labels.npy", clusters)
print("\nSaved cluster labels")