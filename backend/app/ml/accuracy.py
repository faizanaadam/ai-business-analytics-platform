"""Accuracy metrics helpers."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def accuracy_metrics(y_true: list[float] | np.ndarray, y_pred: list[float] | np.ndarray) -> dict[str, float]:
    t = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    if len(t) < 2:
        return {"mae": 0.0, "rmse": 0.0, "r2": 0.0}
    return {
        "mae": round(float(mean_absolute_error(t, p)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(t, p))), 4),
        "r2": round(float(r2_score(t, p)), 4),
    }
