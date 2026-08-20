# ML Algorithms

Hands-on notebooks for the core algorithms introduced in [`../ml_funda.ipynb`](../ml_funda.ipynb). Each one follows the same shape: a short intro + "topics covered" list, then four sections — **Intuition → Training on a dataset → Inspect/interpret → When to use it** — pairing a plain-English definition with runnable code.

All examples use built-in scikit-learn datasets (no downloads) and run top-to-bottom without warnings.

## Notebooks

| # | Notebook | Type | Dataset | Key idea |
|---|----------|------|---------|----------|
| 1 | [linear_reg.ipynb](linear_reg.ipynb) | Regression | diabetes | Fit a line `y = m·x + b`; evaluate with R² / RMSE; read coefficients |
| 2 | [logistic_reg.ipynb](logistic_reg.ipynb) | Classification | breast cancer | Sigmoid → probability; scaled fit; `predict_proba` and thresholds |
| 3 | [decision_tree.ipynb](decision_tree.ipynb) | Classification | iris | Flowchart of yes/no splits; printable rules + feature importance |
| 4 | [random_forest.ipynb](random_forest.ipynb) | Classification | wine | Ensemble of trees (bagging); robust default; feature importance |
| 5 | [knn.ipynb](knn.ipynb) | Classification | iris | Majority vote of nearest neighbours; scale first; choosing `k` |

## Suggested order

Work through them top to bottom — they build conceptually:

1. **Linear regression** — the simplest model; introduces fit/predict/evaluate.
2. **Logistic regression** — same linear idea, turned into classification + probabilities.
3. **Decision tree** — first non-linear, fully interpretable model.
4. **Random forest** — why an *ensemble* of trees beats a single one (overfitting).
5. **k-NN** — a no-training, distance-based baseline; why scaling matters.

## Requirements

```bash
pip install numpy pandas scikit-learn
```

## Quick reference

| Algorithm | Intuition | Good for |
|-----------|-----------|----------|
| Linear regression | Fit a straight line/plane | Predicting a continuous number |
| Logistic regression | Linear score squashed into a probability | Simple, interpretable classification |
| Decision tree | A flowchart of yes/no splits | Interpretable, non-linear patterns |
| Random forest | Many trees voting together | Strong general-purpose baseline |
| k-NN | Label a point by its nearest neighbours | Small datasets, simple boundaries |
