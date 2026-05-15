import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
from scipy import stats


# Load data
timestamps = np.load("data/processed/call_timestamps.npy")
clusters = np.load("data/processed/call_cluster_labels.npy")

print(f"Loaded {len(clusters)} calls with cluster labels")

# Sort by start time to get temporal sequence
order = np.argsort(timestamps[:, 0])
sorted_clusters = clusters[order]
sorted_timestamps = timestamps[order]

print(f"\nCall sequence (first 30): {sorted_clusters[:30].tolist()}")

# Step 1 — Transition matrix
# How often does call type A follow call type B?
transitions = np.zeros((2, 2), dtype=int)
for i in range(len(sorted_clusters) - 1):
    current = sorted_clusters[i]
    next_call = sorted_clusters[i + 1]
    transitions[current][next_call] += 1

print(f"\nTransition counts:")
print(f"  After Cluster 0 → Cluster 0: {transitions[0][0]}")
print(f"  After Cluster 0 → Cluster 1: {transitions[0][1]}")
print(f"  After Cluster 1 → Cluster 0: {transitions[1][0]}")
print(f"  After Cluster 1 → Cluster 1: {transitions[1][1]}")

# Convert to probabilities
transition_probs = transitions / transitions.sum(axis=1, keepdims=True)
print(f"\nTransition probabilities:")
print(f"  After Cluster 0 → Cluster 0: {transition_probs[0][0]:.2%}")
print(f"  After Cluster 0 → Cluster 1: {transition_probs[0][1]:.2%}")
print(f"  After Cluster 1 → Cluster 0: {transition_probs[1][0]:.2%}")
print(f"  After Cluster 1 → Cluster 1: {transition_probs[1][1]:.2%}")

# Step 2 — Gap analysis between calls
gaps = []
for i in range(len(sorted_timestamps) - 1):
    gap = sorted_timestamps[i+1][0] - sorted_timestamps[i][1]
    gaps.append(gap)
gaps = np.array(gaps)
print(f"\nAverage gap between calls: {gaps.mean():.2f}s")
print(f"Median gap: {np.median(gaps):.2f}s")

# Step 3 — Visualize
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Temporal Call Pattern Analysis", fontsize=14)

# Transition matrix heatmap
ax1 = axes[0]
im = ax1.imshow(transition_probs, cmap='Blues', vmin=0, vmax=1)
ax1.set_xticks([0, 1])
ax1.set_yticks([0, 1])
ax1.set_xticklabels(['Cluster 0\n(Long)', 'Cluster 1\n(Short)'])
ax1.set_yticklabels(['Cluster 0\n(Long)', 'Cluster 1\n(Short)'])
ax1.set_xlabel("Next Call")
ax1.set_ylabel("Current Call")
ax1.set_title("Transition Probabilities\n(Markov Matrix)")
for i in range(2):
    for j in range(2):
        ax1.text(j, i, f"{transition_probs[i][j]:.2%}",
                ha='center', va='center', fontsize=12, color='black')
plt.colorbar(im, ax=ax1)

# Call sequence over time
ax2 = axes[1]
ax2.scatter(sorted_timestamps[:, 0], sorted_clusters,
           c=sorted_clusters, cmap='coolwarm', alpha=0.5, s=10)
ax2.set_xlabel("Time (seconds)")
ax2.set_ylabel("Cluster (0=Long, 1=Short)")
ax2.set_title("Call Type Sequence Over Time")
ax2.set_yticks([0, 1])
ax2.set_yticklabels(['Cluster 0\n(Long)', 'Cluster 1\n(Short)'])

# Gap distribution
ax3 = axes[2]
ax3.hist(gaps[gaps < 10], bins=30, color='steelblue', edgecolor='white')
ax3.set_xlabel("Gap Between Calls (seconds)")
ax3.set_ylabel("Count")
ax3.set_title("Time Between Consecutive Calls")
ax3.axvline(gaps.mean(), color='red', linestyle='--', label=f'Mean: {gaps.mean():.2f}s')
ax3.legend()

plt.tight_layout()
plt.savefig("data/processed/temporal_analysis.png")
plt.show()
print("\nSaved temporal analysis")

# Permutation test
print("\nRunning permutation test...")

# Actual short-to-short transition probability
actual_short_to_short = transition_probs[1][1]
actual_long_to_long = transition_probs[0][0]

# Shuffle call order 1000 times and measure transition probs
n_permutations = 1000
random_short_to_short = []
random_long_to_long = []

for _ in range(n_permutations):
    shuffled = sorted_clusters.copy()
    np.random.shuffle(shuffled)
    
    # Calculate transition probs for shuffled sequence
    rand_transitions = np.zeros((2, 2))
    for i in range(len(shuffled) - 1):
        rand_transitions[shuffled[i]][shuffled[i+1]] += 1
    rand_probs = rand_transitions / rand_transitions.sum(axis=1, keepdims=True)
    
    random_short_to_short.append(rand_probs[1][1])
    random_long_to_long.append(rand_probs[0][0])

random_short_to_short = np.array(random_short_to_short)
random_long_to_long = np.array(random_long_to_long)

# p-value = how often random shuffles exceed actual value
p_short = (random_short_to_short >= actual_short_to_short).mean()
p_long = (random_long_to_long >= actual_long_to_long).mean()

print(f"\nPermutation Test Results:")
print(f"Short-to-short: actual={actual_short_to_short:.2%} | random mean={random_short_to_short.mean():.2%} | p={p_short:.4f}")
print(f"Long-to-long:   actual={actual_long_to_long:.2%} | random mean={random_long_to_long.mean():.2%} | p={p_long:.4f}")

if p_short < 0.05:
    print("✅ Short call clustering is statistically significant (p < 0.05)")
else:
    print("❌ Short call clustering is NOT statistically significant")

if p_long < 0.05:
    print("✅ Long call clustering is statistically significant (p < 0.05)")
else:
    print("❌ Long call clustering is NOT statistically significant")

# Visualize
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle("Permutation Test — Is Call Clustering Random?", fontsize=13)

for ax, random_vals, actual_val, label in zip(
    axes,
    [random_long_to_long, random_short_to_short],
    [actual_long_to_long, actual_short_to_short],
    ["Long → Long", "Short → Short"]
):
    ax.hist(random_vals, bins=30, color='steelblue', edgecolor='white', label='Random shuffles')
    ax.axvline(actual_val, color='red', linewidth=2, linestyle='--', label=f'Actual: {actual_val:.2%}')
    ax.axvline(np.mean(random_vals), color='gray', linewidth=1, linestyle=':', label=f'Random mean: {np.mean(random_vals):.2%}')
    ax.set_title(f"{label} Transition")
    ax.set_xlabel("Transition Probability")
    ax.set_ylabel("Count (out of 1000 shuffles)")
    ax.legend()

plt.tight_layout()
plt.savefig("data/processed/permutation_test.png")
plt.show()