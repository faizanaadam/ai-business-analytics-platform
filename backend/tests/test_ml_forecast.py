import numpy as np
import pytest

from app.ml.forecast import forecast_series, ALLOWED_HORIZONS


def _series(n=180, slope=1.0, noise=2.0, seed=3):
    rng = np.random.default_rng(seed)
    dates = [f"2025-01-{(i % 28) + 1:02d}" if i < 28 else (np.datetime64("2025-01-01") + np.timedelta64(i, "D")).astype(str) for i in range(n)]
    vals = (100 + slope * np.arange(n) + rng.normal(0, noise, n)).tolist()
    return vals, dates


def test_forecast_monotone_trend_sensible_mae():
    vals, dates = _series(slope=1.5, noise=1.0)
    fc = forecast_series(vals, dates, 30)
    assert fc.model_name == "ridge_rf_hybrid"
    assert len(fc.values) == 30
    assert fc.accuracy["mae"] < 10.0  # tight series, model should be close
    # forecast continues the upward trend (avg above history avg)
    assert np.mean(fc.values) > np.mean(vals[-60:])


def test_forecast_bounds_widen_with_horizon():
    vals, dates = _series(n=200, noise=3.0)
    fc = forecast_series(vals, dates, 90)
    width_day1 = fc.upper95[0] - fc.lower95[0]
    width_day90 = fc.upper95[-1] - fc.lower95[-1]
    assert width_day90 > width_day1
    # 95% band wider than 80% band everywhere
    for lo80, hi80, lo95, hi95 in zip(fc.lower80, fc.upper80, fc.lower95, fc.upper95):
        assert (hi95 - lo95) >= (hi80 - lo80)


def test_forecast_all_horizons():
    vals, dates = _series()
    for h in ALLOWED_HORIZONS:
        fc = forecast_series(vals, dates, h)
        assert len(fc.values) == h
        assert len(fc.dates) == h


def test_forecast_rejects_bad_input():
    vals, dates = _series()
    with pytest.raises(ValueError):
        forecast_series(vals, dates, 45)  # not allowed
    with pytest.raises(ValueError):
        forecast_series([1.0, 2.0], ["2025-01-01", "2025-01-02"], 30)  # too few


def test_forecast_fallback_short_series():
    vals = (100 + 2 * np.arange(30) + np.random.default_rng(1).normal(0, 1, 30)).tolist()
    dates = [(np.datetime64("2025-01-01") + np.timedelta64(i, "D")).astype(str) for i in range(30)]
    fc = forecast_series(vals, dates, 30)
    assert fc.fallback_used is True
    assert fc.model_name == "seasonal_naive"
    assert len(fc.values) == 30
