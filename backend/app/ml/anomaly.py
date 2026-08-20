"""Anomaly detection: Isolation Forest + Z-score union with severity bands."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest

ROLLING_WINDOW = 28
Z_HIGH = 3.5
Z_MEDIUM = 3.0
Z_LOW = 1.8
ISO_CONTAMINATION = 0.03


@dataclass
class Anomaly:
    date: str
    metric: str
    value: float
    expected: float
    z_score: float
    method: str  # "isolation_forest" | "zscore" | "both"
    severity: str  # high / medium / low


def _rolling_z(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = len(values)
    expected = np.zeros(n)
    z = np.zeros(n)
    for i in range(n):
        lo = max(0, i - ROLLING_WINDOW)
        win = values[lo:i]
        if len(win) < 7:
            expected[i] = values[lo:i + 1].mean() if i else values[0]
            z[i] = 0.0
        else:
            mu = win.mean()
            sd = win.std(ddof=1)
            expected[i] = mu
            z[i] = (values[i] - mu) / sd if sd > 1e-9 else 0.0
    return expected, z


def _severity(z: float) -> str:
    az = abs(z)
    if az >= Z_HIGH:
        return "high"
    if az >= Z_MEDIUM:
        return "medium"
    return "low"


def detect_anomalies(
    metric: str,
    values: list[float],
    dates: list[str],
    sensitivity: float = 0.75,
) -> list[Anomaly]:
    """Union of Isolation Forest and rolling Z-score flags, min window guard."""
    arr = np.array(values, dtype=float)
    if len(arr) < 14:
        return []

    # --- rolling z-score ---
    expected, z = _rolling_z(arr)
    z_flags = set(np.where(np.abs(z) >= Z_LOW - (1 - sensitivity) * 0.8)[0])

    # --- isolation forest on [value, roll_mean, roll_std] features ---
    roll_mean = np.array([arr[max(0, i - 7):i + 1].mean() for i in range(len(arr))])
    roll_std = np.array([arr[max(0, i - 7):i + 1].std() for i in range(len(arr))])
    X = np.column_stack([arr, roll_mean, roll_std])
    contam = max(0.01, min(0.10, ISO_CONTAMINATION * (sensitivity / 0.75)))
    iso = IsolationForest(n_estimators=120, contamination=contam, random_state=7)
    labels = iso.fit_predict(X)
    # ISO with forced contamination flags ~contam fraction even on pure noise;
    # require mild z corroboration so flat series stay clean.
    iso_flags = set(i for i in np.where(labels == -1)[0] if abs(z[i]) >= 1.2)

    union = sorted(z_flags | iso_flags)
    out: list[Anomaly] = []
    for i in union:
        method = "both" if (i in z_flags and i in iso_flags) else ("zscore" if i in z_flags else "isolation_forest")
        out.append(
            Anomaly(
                date=dates[i],
                metric=metric,
                value=round(float(arr[i]), 4),
                expected=round(float(expected[i]), 4),
                z_score=round(float(z[i]), 3),
                method=method,
                severity=_severity(z[i]) if method != "isolation_forest" else "low",
            )
        )
    # suppress chained low-severity noise: keep at most 1 anomaly per 3-day window unless high
    filtered: list[Anomaly] = []
    for a in out:
        if filtered and a.severity != "high":
            last = filtered[-1]
            if (np.datetime64(a.date) - np.datetime64(last.date)).astype(int) <= 2:
                continue
        filtered.append(a)
    return filtered
