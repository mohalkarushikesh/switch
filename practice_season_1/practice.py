import numpy as np
import matplotlib.pyplot as plt 
from sklearn.datasets import make_moons         # toy non-linear dataset generator 
from sklearn.model_selection import train_test_split  

rng = np.random.default_rng(42)     # modern numpy generator
np.random.seed(42)                  # legacy global RNG 

# noise adds Gaussian jitters 
x, y = make_moons(n_samples=1000, noise=0.20, random_state=42)

# stratify=y keeps keeps the 0/1 class indentical in both splits. 
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42, stratify=y) 

# stadardize with train-set statistics only 
mu, sigma = x_train.mean(axis=0), x_train.std(axis=0)

# print("Mean: ", mu)
# print("Standard Deviation: ", sigma)

x_train = x_train - mu / sigma
x_test = x_test - mu / sigma

# reshape the labels to column vectors (n, 1) so they brodcast clearly with predictions 
y_train = y_train.reshape(-1, 1)
y_test = y_test.reshape(-1, 1)

# print(f"train: {x_train.shape}, test: {x_test.shape}")

# plt.figure(figsize=(8, 6))
# plt.scatter(x_train[:, 0], x_train[:, 1], c=y_train.ravel(), cmap='coolwarm', s=12, edgecolors='k', linewidths=0.2)
# plt.title("Two moons stadardized, train set")
# plt.xlabel("x1")
# plt.ylabel("x2")
# plt.show()

def sigmoid(z):
    z = np.asarray(z, dtype=float)
    out = np.empty_like(z)

    positive = z >= 0
    negative = ~positive

    # For z >= 0: exp(-z) is small and safe
    out[positive] = 1.0 / (1.0 + np.exp(-z[positive]))

    # For z < 0: use exp(z)/(1+exp(z)) so exp() only sees negatives
    exp_z = np.exp(z[negative])
    out[negative] = exp_z / (1.0 + exp_z)

    return out
    
def bce_loss(): 
    """Mean binary cross entropy (log-loss)."""
    
    pass 
