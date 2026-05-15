import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Load your saved chunks
X = np.load("data/processed/chunks_X.npy")
y = np.load("data/processed/chunks_y.npy")

print(f"Loaded {len(X)} chunks")

# Step 1 — Normalize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Step 2 — Reduce dimensions with PCA first (K-means struggles with 165k features)
print("Running PCA...")
pca = PCA(n_components=50, random_state=42)
X_reduced = pca.fit_transform(X_scaled)
print(f"Explained variance: {sum(pca.explained_variance_ratio_):.2%}")

# Step 3 — K-means with 2 clusters (orca vs no orca)
print("Running K-means...")
kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
clusters = kmeans.fit_predict(X_reduced)

# Step 4 — Compare clusters to real labels
from sklearn.metrics import adjusted_rand_score
score = adjusted_rand_score(y, clusters)
print(f"\nAdjusted Rand Score: {score:.3f}")
print("(1.0 = perfect match to real labels, 0 = random)")

# Step 5 — Visualize using first 2 PCA components
print("Plotting...")
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.scatter(X_reduced[:, 0], X_reduced[:, 1], c=clusters, cmap='coolwarm', alpha=0.3, s=5)
plt.title("K-means Clusters")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")

plt.subplot(1, 2, 2)
plt.scatter(X_reduced[:, 0], X_reduced[:, 1], c=y, cmap='coolwarm', alpha=0.3, s=5)
plt.title("Actual Labels (0=no orca, 1=orca)")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")

plt.tight_layout()
plt.savefig("data/processed/clustering.png")
plt.show()