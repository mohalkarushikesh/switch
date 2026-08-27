import numpy as np


# A single-layer perceptron: the simplest neural unit. It learns a linear
# decision boundary for binary classification via the classic perceptron rule.
class Perceptron:
    def __init__(self, lr=0.01, n_iters=1000):
        self.lr = lr                             # learning rate: how big a step each weight update takes
        self.n_iters = n_iters                   # number of passes (epochs) over the whole training set
        self.weights = None                      # one weight per input feature (set during fit)
        self.bias = None                         # scalar offset / threshold (set during fit)

    # Activation: outputs 1 if the input is >= 0, else 0 (a hard threshold)
    def step_funct(self, x):
        return np.where(x >= 0, 1, 0)

    def fit(self, X, y):
        X = np.array(X, dtype=float)             # ensure inputs are a float array for the math
        y = np.array(y)                          # true labels (0 or 1)
        n_features = X.shape[1]
        self.weights = np.zeros(n_features)      # start all weights at 0
        self.bias = 0.0                          # start bias at 0

        # Train for n_iters epochs
        for _ in range(self.n_iters):
            # Go through every training sample one at a time
            for idx, x_i in enumerate(X):
                linear_output = np.dot(x_i, self.weights) + self.bias   # weighted sum + bias
                y_predicted = self.step_funct(linear_output)            # apply the step activation
                # Perceptron rule: update is 0 when correct, +lr or -lr when wrong
                update = self.lr * (y[idx] - y_predicted)
                self.weights += update * x_i     # nudge weights toward the correct answer
                self.bias += update              # nudge the bias too

    def predict(self, X):
        X = np.array(X, dtype=float)
        linear_output = np.dot(X, self.weights) + self.bias   # same forward pass as in fit
        return self.step_funct(linear_output)                 # threshold to get 0/1 predictions


if __name__ == "__main__":
    # Train the perceptron to learn the OR logic gate
    X = [[0, 0], [0, 1], [1, 0], [1, 1]]         # the four possible 2-bit inputs
    y = [0, 1, 1, 1]                             # this is OR logic (1 unless both inputs are 0)

    model = Perceptron(lr=0.01, n_iters=10)
    model.fit(X, y)                              # learn weights and bias from the data

    print("Learned Weights:", model.weights)
    print("Learned Bias:   ", model.bias)
    print("Predictions:    ", model.predict(X)) # should match y: [0, 1, 1, 1]
    
    
