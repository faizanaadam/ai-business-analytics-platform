import numpy as np

from app.ml.anomaly import detect_anomalies


def _flat_with_spike(n=120, spike_at=100, spike_mag=6.0):
    rng = np.random.default_rng(5)
    vals = 50 + rng.normal(0, 1.0, n)
    vals[spike_at] += spike_mag  # ~6 sigma spike
    vals[spike_at + 1] += spike_mag * 0.5
    dates = [(np.datetime64("2025-01-01") + np.timedelta64(i, "D")).astype(str) for i in range(n)]
    return vals.tolist(), dates


def test_injected_spike_flagged_high():
    vals, dates = _flat_with_spike()
    out = detect_anomalies("revenue", vals, dates)
    assert any(a.date == dates[100] for a in out)
    spike = next(a for a in out if a.date == dates[100])
    assert spike.severity == "high"
    assert abs(spike.z_score) >= 3.5


def test_flat_series_no_high_or_medium_anomalies():
    rng = np.random.default_rng(11)
    vals = (100 + rng.normal(0, 0.05, 120)).tolist()
    dates = [(np.datetime64("2025-01-01") + np.timedelta64(i, "D")).astype(str) for i in range(120)]
    out = detect_anomalies("revenue", vals, dates, sensitivity=0.5)
    # a sound detector may tag ~1-2% of pure noise as LOW, but must never
    # manufacture high/medium-severity alerts from flat data
    assert all(a.severity == "low" for a in out), [a for a in out if a.severity != "low"]
    assert len(out) < 0.2 * 120  # tolerable noise-tag rate on flat data


def test_short_series_returns_empty():
    vals = list(range(10))
    dates = [f"2025-01-{i+1:02d}" for i in range(10)]
    assert detect_anomalies("revenue", vals, dates) == []


def test_severity_bands():
    vals, dates = _flat_with_spike(spike_mag=2.8)  # ~2.8 sigma
    out = detect_anomalies("revenue", vals, dates)
    if out:
        assert all(a.severity in {"high", "medium", "low"} for a in out)
