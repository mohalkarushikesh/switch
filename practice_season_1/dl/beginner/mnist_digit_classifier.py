# --- Imports ---
import numpy as np                                      # numerical arrays / RNG
import torch                                            # core PyTorch (tensors, autograd)
import torch.nn as nn                                   # layers, activations, loss functions
import matplotlib
import torch.optim.adam
matplotlib.use('Agg')                                   # use a non-interactive backend so plots save to file without a display
import matplotlib.pyplot as plt
from sklearn.datasets import load_digits                # small 8x8 handwritten-digit dataset
from sklearn.model_selection import train_test_split    # split data into train/test sets
from torchinfo import summary                           # print a Keras-style summary of the model

# --- Reproducibility: seed every RNG so each run gives identical results ---
torch.manual_seed(42)       # fix PyTorch RNG for reproducible results
np.random.seed(42)          # fix Numpy RNG for reproducible results

# --- Load and prepare the data ---
digits = load_digits()      # 1797 samples of 8x8 grayscale digit images (flattened to 64 features)
# X → float32: neural nets (especially PyTorch/GPU) do math in float32 by default
# — it's half the memory of float64 and plenty precise for features. This is the standard input dtype.
# y → int64 (long) is required by CrossEntropyLoss for the class-index labels.
x = digits.data.astype(np.float32)      # features as float32
y = digits.target.astype(np.int64)      # labels as int64 (class indices 0-9)

x /= 16.0       # scale pixel values from 0-16 to 0-1 (helps the network train faster/more stably)

n_features = x.shape[1]                 # 64 input features (8x8 pixels)
n_classes = len(np.unique(y))           # 10 output classes (digits 0-9)

# Split 80/20; stratify=y keeps each digit's proportion equal across train and test
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.20, random_state=42, stratify=y)

# Convert the NumPy arrays into PyTorch tensors so they can flow through the model
x_train_t = torch.from_numpy(x_train)
x_test_t = torch.from_numpy(x_test)
y_train_t = torch.from_numpy(y_train)
y_test_t = torch.from_numpy(y_test)

# --- Define the model: a simple fully-connected network, 64 -> 128 -> 64 -> 10 ---
model = nn.Sequential(
    nn.Linear(n_features, 128),         # input layer: 64 features -> 128 hidden units
    nn.ReLU(),                          # non-linearity so the network can learn complex patterns
    nn.Linear(128, 64),                 # hidden layer: 128 -> 64
    nn.ReLU(),
    nn.Linear(64, n_classes)            # output layer: 64 -> 10 raw scores (logits), one per digit
)

batch_size=32

summary(model, input_size=(batch_size, 64))    # print layer shapes and parameter counts

# CrossEntropyLoss applies softmax internally, so the model outputs raw logits (no softmax layer needed)
loss_func = nn.CrossEntropyLoss()

# Adam optimizer updates the weights; lr=1e-3 is a good default learning rate
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

n_epochs = 300
loss_hist = []                          # record the loss each epoch so we can plot it later

# --- Training loop (full-batch gradient descent: all training data used each step) ---
for epoch in range (n_epochs):
    model.train()                       # set the model to training mode

    optimizer.zero_grad()               # clear gradients left over from the previous step
    logits = model(x_train_t)           # forward pass: compute predictions
    loss = loss_func(logits, y_train_t) # measure how wrong the predictions are
    loss.backward()                     # backward pass: compute gradients
    optimizer.step()                    # update the weights using those gradients

    loss_hist.append(loss.item())       # store the scalar loss value for plotting

    if (epoch+1) % 10 == 0:             # print progress every 10 epochs
        print(f"Epoch: {epoch+1:3d}/{n_epochs} | Traning Loss: {loss.item():.4f}")

# --- Evaluate on the held-out test set ---
model.eval()                            # set the model to evaluation mode
with torch.no_grad():                   # disable gradient tracking (faster, less memory) since we're only predicting
    test_logits = model(x_test_t)
    predictions = test_logits.argmax(dim=1)                     # pick the class with the highest score
    accuracy = (predictions == y_test_t).float().mean().item()  # fraction of correct predictions

print(f"Test Accuracy: {accuracy * 100:.2f} % {(accuracy * len(y_test))/len(y_test)} correct)")

# --- Plot the training loss curve to visualise how the loss dropped over epochs ---
plt.figure(figsize=(8, 6))
plt.plot(range(1, n_epochs + 1), loss_hist, color="#2563eb")
plt.title("Traning loss over epochs")
plt.xlabel("Epoch")
plt.ylabel("Cross entropy loss")
plt.grid(True, alpha=0.3)
plt.tight_layout()

# Save the loss curve to disk (Agg backend can't display interactively)
loss_path = "training_loss.png"
plt.savefig(loss_path, dpi=120)
print(f"Training loss plot saved to: {loss_path}")

# --- Inspect a few individual predictions ---
n_samples = 8
sample_idx = np.random.choice(len(x_test_t), size=n_samples, replace=False)   # pick 8 random test images

model.eval()
with torch.no_grad():
    sample_logits = model(x_test_t[sample_idx])
    sample_probs = torch.softmax(sample_logits, dim=1)      # convert logits to probabilities so we can read a confidence
    sample_preds = sample_probs.argmax(dim=1)               # the predicted digit for each sample


# Print each sample's predicted digit, confidence, and the true label
print("\nSample predictions:")
for i, idx in enumerate(sample_idx):
    pred = sample_preds[i].item()
    true = int(y_test[idx])
    conf = sample_probs[i, pred].item()                     # confidence in the predicted class
    mark = "OK" if pred == true else "XX"                   # quick right/wrong flag
    print(f"  [{mark}] predicted {pred} (conf {conf:5.1%})  |  actual {true}")

# --- Draw the sampled digit images in a 2x4 grid, titled with prediction vs truth ---
fig, axes = plt.subplots(2, 4, figsize=(8, 4))
for i, ax in enumerate(axes.ravel()):
    idx = sample_idx[i]
    ax.imshow(x_test[idx].reshape(8, 8), cmap="gray_r")     # reshape the 64 features back into an 8x8 image
    pred = sample_preds[i].item()
    true = int(y_test[idx])
    color = "green" if pred == true else "red"              # green title if correct, red if wrong
    ax.set_title(f"pred {pred} / true {true}", color=color, fontsize=9)
    ax.axis("off")
fig.tight_layout()

# Save the grid of sample predictions to disk (Agg backend can't display interactively)
samples_path = "sample_predictions.png"
fig.savefig(samples_path, dpi=120)
print(f"Sample predictions image saved to: {samples_path}")


"""
Epoch:  10/300 | Traning Loss: 2.2107
Epoch:  20/300 | Traning Loss: 2.0256
.
.
Epoch:  80/300 | Traning Loss: 0.3142
Epoch: 300/300 | Traning Loss: 0.0212
Test Accuracy: 97.78 % 0.9777777791023254 correct)

Sample predictions:
  [OK] predicted 4 (conf 100.0%)  |  actual 4
  [OK] predicted 9 (conf 97.8%)  |  actual 9
  [OK] predicted 9 (conf 100.0%)  |  actual 9
  [OK] predicted 1 (conf 76.7%)  |  actual 1
  [OK] predicted 4 (conf 99.6%)  |  actual 4
  [OK] predicted 1 (conf 99.9%)  |  actual 1
  [OK] predicted 4 (conf 99.6%)  |  actual 4
  [OK] predicted 0 (conf 100.0%)  |  actual 0
"""