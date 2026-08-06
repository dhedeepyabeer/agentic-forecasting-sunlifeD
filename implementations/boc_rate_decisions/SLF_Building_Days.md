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
  - legacy mean RPS: `0.0750`
  - `+GDP` mean RPS: `0.0900`
  - delta (`+GDP - legacy`): `+0.0150`
  - verdict: worse with GDP in this run (material degradation).

Overall conclusion: adding GDP has mixed impact in this experiment run — helpful for the logistic baseline but harmful for the agent path.

---

## Day 3

### Objective

Extend `04_SLF_BoC_agent.ipynb` using the suggestions from the notebook's "Make it yours" section, while keeping the notebook safe to run on a limited Copilot / model budget.

### Changes completed

Files touched for this Day 3 notebook work:
- `implementations/boc_rate_decisions/04_SLF_BoC_agent.ipynb`
- `implementations/boc_rate_decisions/starter_agent/agent.py`
- `implementations/boc_rate_decisions/starter_agent/skills/research-playbook/SKILL.md`
- `implementations/boc_rate_decisions/starter_agent/skills/code-analysis-playbook/SKILL.md`

1. Flip code execution on
- Changes:
  - Added explicit notebook capability toggles: `ENABLE_SEARCH`, `ENABLE_CODE_EXEC`, `STYLE`, and `RUN_AGENT`.
  - Added a concise startup printout so the active run mode is visible before any live call.
  - Exposed code-execution availability directly through the config preview so the loaded skills reflect the toggle state.
  - Added a dedicated live comparison cell that holds model, style, question origin, and forecast origin fixed while comparing rationale with `enable_code_exec=False` versus `enable_code_exec=True`.
- Impact:
  - Code execution is now easy to enable from the notebook without editing library code.
  - The notebook now hits the original target of comparing the forecast rationale with and without code execution, not just flipping the toggle.
  - The notebook remains safer and cheaper to iterate on because live execution is an explicit opt-in.

2. Edit the agent's personality
- Changes:
  - Updated `starter_agent/agent.py` so `_build_starter_instruction(style=...)` now owns style-specific behavior directly in source.
  - Added source-level style presets: `balanced`, `skeptical`, and `cautious`.
  - Added source-level analysis-discipline guidance covering cutoff awareness, base-rate-first reasoning, and dovish/base/hawkish scenario framing.
  - Added a one-driver conclusion rule in each style block so outputs stay auditable and testable.
  - Updated Cell 4 in `04_SLF_BoC_agent.ipynb` to pass `style=STYLE` into `build_starter_agent_config(...)` rather than appending a notebook-only suffix.
  - Replaced the hard-coded `2% CPI inflation target` phrasing in the starter-agent role with `the Bank's inflation-targeting framework`.
- Impact:
  - Personality changes now follow the "Make it yours" suggestion literally by living in `_build_starter_instruction()`.
  - Cell 4 output now demonstrates source-level persona changes, not just notebook-local prompt augmentation.
  - The persona is more robust because it no longer bakes in a potentially stale numeric inflation-target assumption.

3. Sharpen the skills
- Changes:
  - Added a concrete BoC query pack to `research-playbook`, with explicit cutoff-aware searches for BoC communications, CPI/core inflation, labour-market data, market pricing, and trade/oil/FX shocks.
  - Added a concrete BoC diagnostic recipe to `code-analysis-playbook`, including base-rate recomputation, direct-reversal checks, and macro-snapshot summarisation using the real payload fields.
  - Kept the notebook config preview so the loaded skill names remain visible when the corresponding tool is enabled.
- Impact:
  - This item is now implemented directly in the skill files rather than only hinted at in the notebook.
  - The agent can pick up higher-signal search queries and better BoC-specific diagnostics automatically whenever those playbooks are loaded.

4. Change the question and the origin
- Changes:
  - Added `QUESTION_PRESETS` and `QUESTION_KEY` in the Track 2 cell for one-line switching between `base`, `hawkish_risk`, and `dovish_risk` prompts.
  - Reworked Track 1 to support three origin modes:
    - `latest_resolved`
    - `manual`
    - `upcoming`
- Impact:
  - Open-ended scenario exploration is faster because question changes no longer require rewriting the prompt each time.
  - Historical and live-style forecast experiments are easier because forecast origin is now an explicit notebook control.




