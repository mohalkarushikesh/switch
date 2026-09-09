The bias–variance tradeoff — a classic interview topic, and one you'll likely get asked about. Here's the clear version.

**Bias** is error from wrong assumptions — the model is too simple to capture the real pattern. High bias → *underfitting*. It does poorly on both training and test data. (Example: fitting a straight line to curved data.)

**Variance** is error from sensitivity to the specific training data — the model captures noise, not just signal. High variance → *overfitting*. It does great on training data but poorly on unseen data. (Example: a deep decision tree that memorizes every point.)

The **tradeoff**: as you increase model complexity, bias drops but variance rises. Total error is roughly bias² + variance + irreducible noise, so it forms a U-shape — there's a sweet spot in the middle where the two are balanced and test error is lowest.The black U-shaped curve is what you're managing: you want to land at its lowest point, not at either extreme.

Two quick things worth knowing for interviews:

**How to fix each side.** High bias (underfitting) → use a more complex model, add features, reduce regularization, train longer. High variance (overfitting) → get more training data, simplify the model, add regularization (L1/L2, dropout), use bagging/ensembling, or early stopping.

**A subtle modern caveat.** The classic U-shape holds for traditional ML, but deep learning shows a "double descent" phenomenon — past the interpolation point, test error can drop *again* as you keep growing an over-parameterized network. If an interviewer is sharp, mentioning double descent signals you're current.

Given your background, this could come up as either a definition question or applied ("your model has 98% train accuracy but 70% test — what's happening and what do you do?"). Want me to run through a few likely interview questions on this, or move to another core ML topic?
