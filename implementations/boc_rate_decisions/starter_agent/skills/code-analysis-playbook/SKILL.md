---
name: code-analysis-playbook
description: >-
  How to use the code execution sandbox well — parse the JSON payload (not
  disk files), compute a couple of useful diagnostics before forecasting, and
  keep the session stateful within a turn. Load this before writing code. No
  scripts.
---

# Code-analysis playbook

A short guide to using the `run_code` sandbox productively. This is a starter
skill — extend it with the diagnostics that matter for your problem.

## Where your data lives

All data comes from the **JSON payload in your context** — there are no disk
files and no network. The history arrives as a CSV *string* (e.g.
`target_history_csv`). Parse it with `io.StringIO`, never as a file path:

```python
import io, pandas as pd
df = pd.read_csv(io.StringIO(payload["target_history_csv"]))
```

The sandbox is **stateful within a turn**: parse once in your first code block,
then reuse the DataFrame in later blocks instead of re-parsing.

## Compute before you forecast

Run a couple of cheap diagnostics so your forecast is grounded in arithmetic,
not vibes:

1. **Recent trend** — slope/return over the last N observations.
2. **Volatility** — recent standard deviation of changes; it sets how wide your
   quantile bands should be.
3. **Sanity check** — does your point forecast sit within a plausible multiple
   of recent moves? If not, revisit it.

Use the printed numbers to set the point forecast and to *calibrate the spread*
between your low and high quantiles — wider when recent volatility is high.

## Domain focus (edit this for your use case)

For a BoC rate decision your payload is categorical: it carries the policy-rate
change points, the per-outcome base rates, and a macro snapshot — not a price
CSV, so adapt the parsing above to those fields. Useful diagnostics: recompute
the empirical base rates, measure how far the current macro snapshot sits from
typical pre-cut vs pre-hold conditions, and count how often the Bank reversed
direction between adjacent meetings.

## Concrete BoC diagnostics

If `run_code` is available, these are good first diagnostics before setting
probabilities:

1. **Recompute the historical base rates** from `payload["meeting_outcomes"]` and compare them with the provided `historical_base_rates`.
2. **Check tail plausibility** by counting how often the Bank moved directly from `cut` to `hike` or from `hike` to `cut` in adjacent meetings.
3. **Summarise the current macro snapshot** from `payload["macro_snapshot"]`:
   - `yield_spread`
   - `rate_momentum`
   - `inflation_gap`
   - `unemployment_momentum`
   - optional `gdp_growth_yoy`

Example pattern:

```python
meeting = payload["meeting_outcomes"]
history = meeting["history"]
counts = meeting["counts"]
base_rates = meeting["historical_base_rates"]
macro = payload["macro_snapshot"]

transitions = list(zip(history[:-1], history[1:]))
direct_reversals = sum(
   1
   for prev, curr in transitions
   if {prev["decision"], curr["decision"]} == {"cut", "hike"}
)

summary = {
   "base_rates": base_rates,
   "n_meetings": meeting["n_meetings"],
   "direct_cut_hike_reversals": direct_reversals,
   "yield_spread": macro.get("yield_spread"),
   "rate_momentum": macro.get("rate_momentum"),
   "inflation_gap": macro.get("inflation_gap"),
   "unemployment_momentum": macro.get("unemployment_momentum"),
   "gdp_growth_yoy": macro.get("gdp_growth_yoy"),
}
print(summary)
```

Interpretation guide:

- Large negative `yield_spread` usually supports cuts more than hikes.
- Positive `inflation_gap` argues against early easing.
- Positive `unemployment_momentum` supports more dovish probabilities.
- Near-zero direct reversals mean tail outcomes should usually remain small unless several signals align.

## Room to grow

- Add your own diagnostic patterns (regime detection, seasonality, covariates).
- Drop reusable reference values into a `references/` file and `load_skill_resource` them.
