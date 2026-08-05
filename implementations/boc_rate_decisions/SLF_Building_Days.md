# SLF Building Days

This file records implementation changes by day for the `implementations/boc_rate_decisions` workstream.

## Day 1

### Objective

Make StatCan GDP available in the BoC use case and surface it in the exploratory notebook.

### Changes completed

1. Data-service integration
- File: `implementations/boc_rate_decisions/data.py`
- Added `GDP_SERIES_ID = "canada_real_gdp_all_industries"`.
- Added `GDP_TABLE_ID = "36-10-0434-01"`.
- Registered GDP via `StatCanAdapter` in `build_boc_service(...)` with Canada / SAAR / chained-2017 / all-industries filters.
- Exported GDP constants via `__all__`.

2. Data fetch script
- File: `scripts/fetch_boc.py`
- Added GDP table cache artifact (`36100434-eng.zip`) so `fetch_boc.py` pulls GDP alongside other BoC covariates.

3. Documentation and notebook updates
- File: `implementations/boc_rate_decisions/README.md`
- Added GDP to the data table and cache command note.
- File: `implementations/boc_rate_decisions/01_boc_data_exploration.ipynb`
- Updated setup and macro-covariate text from 3 to 4 covariates.
- Added GDP import, GDP YoY series computation, and a 4th macro subplot for GDP growth.

### Validation completed

- Verified StatCan table/member filters for GDP.
- Executed key cells in `01_boc_data_exploration.ipynb` (service setup + macro chart) successfully.
- Confirmed GDP loads through `build_boc_service(...)` in a direct Python check.

---

## Day 2 

### Objective

Update `02_boc_rate_direction_experiment.ipynb` to test whether adding GDP changes predictions/scores, and document the result path.

### Changes completed

1. Predictor extension for GDP impact testing
- File: `implementations/boc_rate_decisions/predictors/logistic_baseline.py`
- Added optional GDP feature plumbing to `build_feature_row(...)`:
  - new optional arg `gdp_df`
  - new flag `include_gdp`
  - new feature key `gdp_growth_yoy`
- Added `FEATURE_NAMES_WITH_GDP` while keeping `FEATURE_NAMES` as the legacy set.
- Extended `BoCLogisticPredictor` to support:
  - `include_gdp` toggle
  - optional `predictor_id` override
  - GDP-aware training/inference feature assembly.
- GDP-enabled default identifier is `boc_logistic_macro_gdp` when `include_gdp=True`.

2. Test coverage updates
- File: `implementations/tests/boc_rate_decisions/test_logistic_baseline.py`
- Added/updated tests for:
  - GDP feature inclusion when enabled
  - poison-row leak safety with GDP enabled
  - insufficient-history behavior in GDP-enabled mode.

3. Main experiment notebook updates
- File: `implementations/boc_rate_decisions/02_boc_rate_direction_experiment.ipynb`
- Updated predictors section to include both conventional rows:
  - legacy logistic (no GDP)
  - logistic + GDP.
- Updated predictor construction cell to instantiate both variants and include both in `all_predictors`.
- Added a new "GDP delta check" subsection + code cell that prints:
  - legacy vs `+GDP` mean RPS
  - score delta (`+GDP - legacy`)
  - top meetings by absolute probability shift.

4. README reconciliation for model behavior
- File: `implementations/boc_rate_decisions/README.md`
- Updated conventional-predictor description to document legacy and optional GDP-expanded feature sets.

5. Agent GDP variant + parity comparison
- File: `implementations/boc_rate_decisions/analyst_agent/agent.py`
- Added optional GDP plumbing for the agent prompt builder:
  - `BoCDecisionPromptBuilder(include_gdp=...)`
  - GDP series fetch + shared leak-safe feature assembly via `build_feature_row(...)`
- Extended config/factory signatures so GDP/non-GDP agent variants are explicit and have distinct IDs:
  - `build_boc_basic_config(..., include_gdp=...)`
  - `build_boc_news_config(..., include_gdp=...)`
  - `build_boc_agent_predictor(..., include_gdp=...)`
- File: `implementations/boc_rate_decisions/02_boc_rate_direction_experiment.ipynb`
- Added both agent variants to predictor setup and leaderboard labels.
- Added a new `GDP delta check (agent model)` section mirroring the logistic delta check:
  - legacy vs `+GDP` mean RPS,
  - per-meeting probability deltas,
  - top meetings by absolute shift,
  - run-specific verdict printout.

6. Agent prompt-builder tests
- File: `implementations/tests/boc_rate_decisions/test_analyst_agent.py`
- Added unit tests to verify:
  - default agent prompt snapshot excludes GDP,
  - GDP-enabled prompt snapshot includes `gdp_growth_yoy`.

### Overall verdict on GDP covariate impact

- Metric used: Ranked Probability Score (RPS), where lower is better.
- Conventional logistic predictor:
  - legacy mean RPS: `0.3680`
  - `+GDP` mean RPS: `0.3621`
  - delta (`+GDP - legacy`): `-0.0059`
  - verdict: small but clear improvement from GDP.
- Agent predictor:
  - legacy mean RPS: `0.0900`
  - `+GDP` mean RPS: `0.0892`
  - delta (`+GDP - legacy`): `-0.0008`
  - verdict: very modest improvement, concentrated in a small number of meetings.

Overall conclusion: adding GDP is directionally beneficial for both predictor families in this experiment run, with a more material gain for the logistic baseline and only a marginal lift for the agent path.

