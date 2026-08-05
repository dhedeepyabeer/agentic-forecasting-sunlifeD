"""Unit tests for BoC analyst-agent prompt builder feature toggles.

The prompt builder should mirror logistic-baseline feature availability, with
GDP YoY exposed only when explicitly enabled.
"""

from __future__ import annotations

import json

import pandas as pd
import pytest
from aieng.forecasting.evaluation.task import ForecastingTask, TaskCategory
from boc_rate_decisions.analyst_agent import BoCDecisionPromptBuilder
from boc_rate_decisions.data import DIRECTION_SERIES_ID


_CATEGORIES = [
    TaskCategory(label="cut", value=-1.0),
    TaskCategory(label="hold", value=0.0),
    TaskCategory(label="hike", value=1.0),
]


class _FakeContext:
    def __init__(self, as_of: pd.Timestamp, series_by_id: dict[str, pd.DataFrame]) -> None:
        self.as_of = as_of.to_pydatetime()
        self._series_by_id = series_by_id

    def get_series(self, series_id: str) -> pd.DataFrame:
        return self._series_by_id[series_id]


def _task() -> ForecastingTask:
    return ForecastingTask(
        task_id="boc_rate_direction_next_meeting",
        target_series_id=DIRECTION_SERIES_ID,
        horizons=[28],
        frequency="D",
        description="BoC 3-way direction test.",
        payload_type="categorical",
        categories=_CATEGORIES,
    )


def _daily(start: str, end: str, value: float) -> pd.DataFrame:
    dates = pd.date_range(start, end, freq="D")
    return pd.DataFrame({"timestamp": dates, "value": value, "released_at": dates + pd.Timedelta(days=1)})


def _monthly(start: str, periods: int, values: list[float]) -> pd.DataFrame:
    dates = pd.date_range(start, periods=periods, freq="MS")
    return pd.DataFrame({"timestamp": dates, "value": values, "released_at": dates + pd.Timedelta(days=21)})


def _context(origin: pd.Timestamp) -> _FakeContext:
    start = origin - pd.DateOffset(months=36)
    n_months = 37

    direction_dates = [pd.Timestamp("2024-01-24"), pd.Timestamp("2024-03-06"), pd.Timestamp("2024-06-05")]
    direction_df = pd.DataFrame(
        {
            "timestamp": direction_dates,
            "value": [0.0, 0.0, -1.0],
            "released_at": direction_dates,
        }
    )

    cpi_values = [100.0 * (1.02 ** (i / 12)) for i in range(n_months)]
    series = {
        DIRECTION_SERIES_ID: direction_df,
        "boc_overnight_target_rate": _daily(str(start.date()), str(origin.date()), 5.0),
        "boc_govt_bond_yield_2yr": _daily(str(start.date()), str(origin.date()), 4.0),
        "cpi_all_items_canada": _monthly(str(start.date()), n_months, cpi_values),
        "fred_canada_unemployment_rate": _monthly(str(start.date()), n_months, [6.0] * n_months),
        "canada_real_gdp_all_industries": _monthly(str(start.date()), n_months, [200.0] * n_months),
    }
    return _FakeContext(origin, series)


def test_prompt_builder_excludes_gdp_by_default() -> None:
    origin = pd.Timestamp("2024-06-04")
    payload = json.loads(BoCDecisionPromptBuilder()(task=_task(), context=_context(origin)))

    snapshot = payload["macro_snapshot"]
    assert isinstance(snapshot, dict)
    assert "gdp_growth_yoy" not in snapshot


def test_prompt_builder_includes_gdp_when_enabled() -> None:
    origin = pd.Timestamp("2024-06-04")
    payload = json.loads(BoCDecisionPromptBuilder(include_gdp=True)(task=_task(), context=_context(origin)))

    snapshot = payload["macro_snapshot"]
    assert isinstance(snapshot, dict)
    assert "gdp_growth_yoy" in snapshot
    assert snapshot["gdp_growth_yoy"] == pytest.approx(0.0)
