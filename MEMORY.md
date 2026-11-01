# Memory Log

## 2026-11-01 — Sphinx math added across `plans.stochastic` (except `bayes`)
Requested by the user; `bayes` left out on purpose, since that part is still pending. Added to `metrics`, `frequency`, `binning`, `descriptive`, `sampling`, `curves`, `normality`, with symbols defined in module docstrings. Docstrings only: code compared equal to the commit by AST, and formulas evaluated against the functions. Noted, not changed: `get_cdf_gumbel` passes `np.std` (n in the denominator) as the "sample standard deviation" of `gumbel_se`.

## 2026-11-01 — Sphinx math added to `stochastic.arma` docstrings
Requested by the user. Model, components, fit estimators, decomposition, baseline and topline, and conversions, using `.. math::` and `:math:`; those docstrings are now raw strings. Only `arma` for now; other `stochastic` modules (Gumbel, metrics) have no math yet.

## 2026-11-01 — `plans.stochastic.arma`: trend, season and AR(1) library (stage 3)
Array-only library: `fit_params`, `decompose`, `build`, `describe`, `make_params`, components and conversions. No `TimeSeries` changes; tutorial and wrappers come later. Departures from the brief: `simulate_ar1` has no `burn` (first shock scaled to the stationary variance, because `burn=100` is short at high `phi` and a `phi`-dependent burn-in breaks common random numbers); new `draw_shocks` keeps shock generation separate; only the upper `power` bound (10) warns, since `power=1` is the right answer for temperature; no "large offset" test, since the fitted `start` already centers the remainder.

Known limits, measured: Gaussian noise is additive, so a rain-like series with a positive floor still went negative in 3.25% of steps (floor 6.25, 1200 steps); `describe(positive=True)` only checks the deterministic floor. Pure noise fits a spurious sharp season (`power` at 10), where the bound warning is the only signal.

## 2026-11-01 — `plans.stochastic` completed; `analyst` purged of pure computation (stage 2)
New modules: `frequency`, `normality`, `binning`, `descriptive`, `sampling`, `curves`, `bayes`. `Univar` statics are thin delegates kept for backward compatibility; `plans` source calls `stochastic` directly. Computation also left instance methods (`get_normality`, `get_frequency`, `get_basic_stats`, `get_cdf_weibull`, `get_cdf_gumbel`, `Bivar.fit`, `Bayes.conditionalize`). `geo.normalize` is now a re-export of `stochastic.sampling.normalize`. Outputs recorded before the refactor match at full precision (50 cases).

Bugs fixed: `get_nbins_by_rule` and `get_histogram(rule=...)` raised `TypeError`; `quantiles_classify` raised `NameError` (returned a name that only existed in a dead string); `Bayes.conditionalize` raised `ValueError` under pandas 3 (wrote into read-only `.values`). The Bayes reference comes from the old code with only that accumulation loop patched, since the original could not run.

Behavior changes in `sample_gamma` (brief tier 1): new `rng`; seeded global-state results unchanged; invalid inputs and constant samples raise `ValueError` (constant samples used to return NaN, unknown `shape_mode` used to raise `KeyError`); warns when `scale` is set with both bounds. `classify` docstring corrected to match the code: a value on an edge goes to the class above. Tier 2 (`mode="theoretical"`) postponed.

## 2026-11-01 — Source callers use `plans.stochastic.metrics` directly, not `Bivar` wrappers
User decision: other modules call `stochastic` directly; `Bivar` statics remain only for backward compatibility. Changed `TimeSeriesCluster.get_correlation` (dropped its local `Bivar` import), `LinearStorage.evaluate` and `Bivar.update_model`. Imported as `_metrics` so `from .core import *` does not leak the name. This also fixes `LinearStorage.evaluate`, which raised `NameError` because `upscaled.py` never imported `Bivar`.

## 2026-11-01 — `plans.stochastic.metrics` extracted from `Bivar` (stage 2)
`pearson`, `spearman`, `rsq`, `rmse`, `mae`, `bias`, `get_metrics` are now plain functions; `Bivar` statics keep their signatures and delegate. Module list approved by the user: metrics, frequency, normality, binning, descriptive, sampling, curves, bayes (no `regression.py`, its targets no longer exist). Modules declare `__all__` to keep the package top clean. New `tests/unit/test_stochastic.py` holds golden values recorded from the original code and a source-scan independence test.

## 2026-11-01 — `plans.stochastic` package skeleton created (stage 2, step B)
Requested by the user. Empty package with docstring only, plus `docs/api_stochastic.rst` registered in `docs/api.rst`. Independence from `plans.datasets`, `plans.viewer` and `plans.geo` holds at runtime, but `plans/__init__.py` always loads `plans.project` and `plans.root`, so the brief's runtime criterion for `plans.root` cannot hold; the source-scan rule still can.

## 2026-11-01 — `plans.analyst` moved to `plans.datasets.analyst` (stage 1 of stochastic refactor)
Whole file moved, explicitly requested by the user as first stage (next: `plans.stochastic` package and purge of pure computations, then `arma`). `plans/analyst.py` is now a deprecation shim (star import plus `DeprecationWarning`), so old imports and pickles still resolve to the same classes; its removal date is still undecided. `datasets/__init__.py` imports `.analyst` before `.core`; this adds `Bayes`, `Bivar`, `linear`, `power`, `power_zero` and `pprint` to the `plans.datasets` namespace. References updated in src, tests, API docs and 7 notebooks (literal replace, stored outputs included). No logic changed.

## 2026-10-30 — TimeSeriesEnsemble: reducers fixed, reducer highlight view, tutorial `timeseries_10_ensemble`
Series-view machinery moved from `TimeSeriesCluster` up to `TimeSeriesCollection` (specs, `series`/`series-simple` axes and dispatch, `_get_labels`, `_plot_series`), so Cluster and Ensemble share it; subclasses opt in with `_set_series_layouts()` (mixed collections don't, since different variables can't share axes). `_plot_series` gained `extra` (foreground non-member series) and `force_background`; foreground zorder 3, bands 2, background 1; legend factored into `_set_series_legend`. Ensemble: fixed `rng` (np.r crash), `percentile` column (was "max"), `percentiles` naming ("p050" -> "p50", "p05"; non-integers "p2.5"), `stats` (std used np.max; `basic` ignored); all reducers NaN-aware (`np.nan*`); new `median()`, `get_reducer_series(name)` (returns base-type series; mean/median/min/max/pNN). Default ensemble view: `series` layout, members background, `view_specs["reducers"]` (["mean"]) as colored foreground series across all 3 panels, `view_specs["bands"]` ([[5, 95]]) shaded on the series panel; `highlight` still selects members. New `tests/unit/test_datasets_TimeSeriesEnsemble.py` (5 tests). Tutorial covers reducers, custom reducer (hot-day probability), reducers as series, views; notes the mean's narrow distribution (averaging cancels weather; mean is a summary, not a realization). Cluster tutorials 08/09 re-run OK.

## 2026-10-30 — Univar default y range gets a 5% margin
Default `view_specs["range"]` in `Univar.update` was exactly [min, max]: the 0 tick of near-zero data fell just outside the axis (min 0.143), and the extreme values sat on the panel edges. Now [min - 5% span, max + 5% span], same convention as the cluster series view. Inherited by `GeoUnivar` and `TimeSeries` default views (user-set `range` untouched). Removed the now-wrong edge note from `univar_02_plots` and rebuilt it (one-sentence diff).

## 2026-10-30 — Bivar `model` layout: 3-row gaps between stacked panels
Titles of the error and variance panels sat level with the x label of the panel above (2-row gaps had to hold ticks, x label and title). Model panel now `gs[2:9]`, error `gs[12:16]`, variance `gs[19:23]`; measured title clearance ~30 px below each x label at 150 dpi, bottom x label inside the figure. `bivar_02_models` outputs refreshed.

## 2026-10-30 — Bivar `model` layout restacked
Left column stacked with shared x: model (top), error, variance (bottom, same size as error); error histogram and Q-Q beside the error row. Model layout now square (120 x 120 mm). Model panel gained x tick labels and x label. Error y ticks use an explicit sign (`FuncFormatter`: "+2", "0", "-2"), also shown on the histogram and Q-Q y axes (labels previously hidden). Panel order in `_build_axes` kept, so `_plot_model` unpacking is unchanged. `bivar_02_models` outputs refreshed (sources unchanged).

## 2026-10-30 — New tutorial `univar_02_plots`; plots moved out of `univar_01`
`univar_02_plots`: skewed in-memory sample (`set_array`), standard view, layouts, data panel scatter vs boxplot (`data_plot`, `box_showfliers`, `plot_mean_data`; mean above median for skewed data), colorized scatter (`scheme_cmap` equal/quantiles), fine-tuning (notes default range edge clipping), saving via `view_specs` + `view(show=False)`. `univar_01`: removed fine-tuning and layout cells (moved), kept one standard `.view()` plus a seealso pointer. Edited `univar_01` as raw JSON (`json.dumps(indent=1, ensure_ascii=False)` + newline reproduces PyCharm's format byte-for-byte; `nbformat.write` reformats the whole file). Registered after `univar_01` in `docs/examples.rst`.

## 2026-10-30 — Univar boxplot option for the data panel
New `view_specs["data_plot"]` ("scatter" default | "boxplot") and static `Univar.plot_boxplot(data, ax, specs, formatter)` (sibling of `plot_scatter`; same y range/labels/color/mean line; specs `subtitle_box`, `box_width`, `box_showfliers`). Applies to `Univar` and `GeoUnivar`; `TimeSeries` replaces the data panel so is unaffected. Added `tests/unit/test_analyst_Univar.py` (both options). Noted, not changed: default `range` = [min, max] puts the extreme value on the axis edge.

## 2026-10-30 — Large-collection view modes + `timeseries_09_cluster_large`
Single threshold `view_specs["n_series_max"]` (10, set on `TimeSeriesCollection`, shared by cluster views; matches tab10's 10 distinct colors). Collection availability view: Gantt line width now fits row height (`min(gantt_linewidth, 0.7 * row height in pt)`), so many series become thin lines; above the threshold, Gantt/prevalence labels hidden ("n series" axis label). Prevalence: bars now aligned to Gantt rows; % values moved from bar tips to tick labels (percent only -- names read across from the Gantt; "name (pct)" labels collided with the Gantt). Cluster `series` layouts: new `highlight` list (colored + legend + means, drawn on top); above threshold without highlight, all series in background style (`color_background`, thin, `alpha_hist_background` 0.1 so stacked histograms shade density), no legend/means. Correlation: annotations and tick labels hidden above threshold; new `range_corr` spec (default [-1, 1]). New test `test_view_large`. New tutorial `timeseries_09_cluster_large` (40 stations, in-memory `set_data`+`append`, weather-center anomalies decaying with distance; correlation-vs-distance plot). 07/08 re-run OK; 08 outputs refreshed.

## 2026-10-30 — Cluster `series` histograms back to filled bars (user preference)
Default `histtype="bar"`, `alpha_hist=0.4`; `"step"` remains available via `view_specs["histtype"]`. Tutorial `timeseries_08_cluster` outputs refreshed. Open issue found (not fixed, awaiting decision): with many series the legend breaks -- `series` legend (6 cols, anchored above the panel) grows upward over the title and off the left edge from ~12 series; `series-simple` single-column legend runs off the figure bottom (30 series: 16 shown); `tab10` gives only 10 distinct colors, so lines repeat colors beyond 10 series.

## 2026-10-30 — Cluster `series` layout: overlaid series, histograms and CDFs
`TimeSeriesCluster` `series` layout now mirrors the single `TimeSeries` mini view (3 panels) for all stations at once, generalizing `view_compare_times_series` by looping the existing static plotters (`TimeSeries.plot_series`, `Univar.plot_histh`, `Univar.plot_cdf`) with per-station specs copied from each series' `view_specs`. Common y range across panels, common histogram bin edges (comparable bars), tab10 colors, unlabeled dashed mean lines, legend above the series panel. Old overlay-only view renamed `series-simple`. Two backward-compatible plotter options via `specs.get`: `linewidth` in `TimeSeries.plot_series`, `histtype` in `Univar.plot_histh` (cluster uses `"step"`; filled overlaid bars were unreadable). Tests and `timeseries_08_cluster` updated (notes S4's higher mean from its shorter record).

## 2026-10-30 — Fixed `TimeSeries.standardize` trailing NaN + `get_epochs` last-row off-by-one
`standardize` grid used `date_range(start, end.normalize() + 1 day)` inclusive, spilling one slot into the next day (daily: +1 NaN row; sub-daily: next day 00:00; MS/YS unaffected); repeated standardizing compounded it (collection tutorial showed series ending 2 days late). Now `inclusive="left"`, keeping the intended whole-day padding for sub-daily series. Fixing it exposed a masked bug: `get_epochs` assigned the last row's epoch to the second-to-last row, leaving the last row in epoch 0, so `interpolate_gaps` blanked the last real value (the spurious NaN row used to absorb this). Fixed with `epoch_v[-1]`; also no longer breaks on 1-row data. Added `tests/unit/test_datasets_TimeSeries.py` (grid ends for D/h/MS; edges kept by `interpolate_gaps`). Old-vs-new tutorial runs (old code copied to scratchpad): only printed outputs of `timeseries_03/04/07` change; no prose quotes affected numbers; 05/06/08 unchanged; 01/02 diffs are unseeded randomness. Supersedes the "known, not fixed" note in the Cluster entry.

## 2026-10-30 — Time series family: Cluster developed, Samples -> Ensemble
Reason: one inheritance chain mixed two concepts (multi-site cluster vs same-site ensemble), with the spatial tool below the ensemble reducers. New structure: `TimeSeriesCluster(TimeSeriesCollection)` and `TimeSeriesEnsemble(TimeSeriesCollection)` as siblings; `TimeSeriesSpatialSamples` removed (content moved to Cluster). chrono: `RainSeriesSamples` -> `RainSeriesCluster`, `TemperatureSeriesSamples` -> `TemperatureSeriesCluster` (no usages existed). Cluster: repaired `regionalize` (stale catalog keys `VarField`/`Name`/`Alias` made it raise KeyError; merged-grid values were written without datetime alignment; weights and sources used different orderings), `get_weights_by_name` moved/fixed, new `get_correlation(method, min_overlap)` (uses `Bivar.pearson/spearman` on overlapping steps), new view layouts `series` (tab10 per station) and `correlation` (heatmap); default `full`/`simple` availability views inherited. Ensemble reducer bugs (`rng` np.r, `percentile` key, `percentiles` naming, `stats` std) intentionally left for the Ensemble phase. Added `tests/unit/test_datasets_TimeSeriesCluster.py` (6 tests, in-memory) and tutorial `timeseries_08_cluster` (5-station synthetic network; IDW vs average gap filling checked against kept truth). Known, not fixed: `TimeSeries.standardize()` grid ends at `end.normalize() + 1 day` inclusive, adding a trailing NaN step to every standardized series. Stochastic module postponed by user.

## 2026-10-30 — `bivar_02_models`: stages skewed to low values
Replaced uniform `np.linspace(0.3, 3.0)` stages with `0.3 + rng.gamma(shape=1.5, scale=0.4)` (median 0.82 m, 68% below 1 m, tail to ~3.5 m), mimicking a gauging record dominated by low flows. Model story unchanged: Power recovers offset (c0 = -0.185), Power_zero exponent inflates to 1.87, Linear worst (R2 0.927). Only this notebook re-executed; `bivar_01` unchanged.

## 2026-10-30 — `viewer.FIG_DPI = 150` applied in `build_fig`
Inline/window figures were small (mm-based print sizes at matplotlib's default 100 dpi; e.g. `S` layout ~320 px wide). `build_fig` now sets `rcParams["figure.dpi"] = FIG_DPI` (150). Saving unaffected: all 14 `savefig` calls in `src/plans` pass an explicit dpi (`ship_fig` uses `specs["dpi"]` = 300); verified saved PNG pixel size unchanged. Only figures built via `viewer.build_fig` are affected.

## 2026-10-30 — `bivar_02_models` title: "- models" -> "- Models"
Title and the `{doc}` link text in `bivar_01`, matching the "- Basics" convention.

## 2026-10-30 — Tutorial titles: "- the basics" -> "- Basics"
Applied to all tutorial titles (bivar_01, univar_01, timeseries_01, visuals_01, raster_01; project_01 "basics" -> "Basics") and to the `{doc}` cross-reference link texts. Raw text replacement, notebooks not re-executed.

## 2026-10-30 — Enabled MyST `dollarmath` in `docs/conf.py`
`$...$` math in notebook markdown rendered as literal text: neither myst-parser 4.0.1 nor myst-nb 1.4.0 enables `dollarmath` by default. Added `myst_enable_extensions = ["dollarmath"]` (keeps notebooks portable to Jupyter/Colab, unlike `{math}` roles). Also fixes `timeseries_06_downscale`. No `.md` docs sources contain literal `$`. Verified via a minimal Sphinx build (0 -> 9 math nodes in `bivar_01`).

## 2026-10-30 — `Bivar.pearson`/`spearman` take `(x, y)`; x-hist mean line
Correlations are symmetric and apply to any two variables, so they take `x`/`y`; agreement metrics (`rsq`, `rmse`, `mae`, `bias`) keep `(observed, predicted)`. `get_metrics` maps observed->x, predicted->y for r/rho. Also fixed `_plot_full`: x marginal histogram (inline `ax.hist`) ignored `plot_mean` while y one (`Univar.plot_histh`) drew it; added `axvline` + `todo [DRY]` for a future `Univar.plot_histv`. Tests and both Bivar tutorials updated.

## 2026-10-30 — Split Bivar tutorial into `bivar_01` (basics) and `bivar_02_models`
`bivar_01`: observed vs simulated discharge dataset; object, loading, `full` layout plotting, static metrics, and an association-vs-agreement table (doubled series: r = rho = 1 but R2 < 0). `bivar_02_models`: synthetic rating curve with stage offset h0 = 0.2 so each model tells a story (Linear misses curvature, Power_zero inflates exponent, Power recovers offset via c0); one section per model (fit, Setup, Metrics, model panel), then comparison table, Linear R2 = r^2 check, error normality for all models, and `update_model`. Both listed in `docs/examples.rst`.

## 2026-10-30 — `Bivar` metrics: all static with `(observed, predicted)`, model-level only
All six metrics (`pearson`, `spearman`, `rsq`, `rmse`, `mae`, `bias`) now take `observed` and `predicted` (was `pred`/`obs` and `x`/`y`); new static `get_metrics(observed, predicted)` returns a dict of plain floats (r, rho, R2, RMSE, MAE, Bias). Models store it in `models[...]["Metrics"]`, replacing the `"RMSE"`/`"R2"` keys. Removed data-level `.r`/`.rho` from `update()`: user stated metrics are only for assessing model fits. Updated callers in `hydrology/upscaled.py`, unit tests and `bivar_01` tutorial. Supersedes the previous entry's data-level r/rho design.

## 2026-10-30 — Split `Bivar` association metrics: Pearson r, Spearman rho, R2
New statics `Bivar.pearson(x, y)` and `Bivar.spearman(x, y)` (Pearson of `scipy.stats.rankdata` ranks, ties averaged). Data-level attributes `.r` and `.rho` computed in `update()`, replacing `.corr` and `get_correlation()` (removed). Model-level `R2` (`rsq`, 1 - SS_res/SS_tot) now stored in `models[...]["R2"]` beside `RMSE`. Kept `rsq` name since `hydrology/upscaled.py` uses it. Reason for split: r/rho describe the data, R2 describes a fit; they coincide (R2 = r^2) only for the least-squares linear model. Tutorial `bivar_01` and unit tests updated.

## 2026-10-30 — Added `docs/tutorials/bivar_01.ipynb` tutorial
Basics of the refactored `Bivar`: attributes/labels, `load_data`, computed attributes, `full` and `model` layouts, fitting and comparing models, `update_model`, error normality and static metrics. Mirrors `univar_01` structure; executed with outputs stored. Listed in `docs/examples.rst` right after `univar_01`.

## 2026-10-30 — Added `testing/analyst_Bivar_views.py` view script
User asked for it under `scripts/`, which is off-limits by CLAUDE.md hard rules; placed in `testing/` next to `analyst_Univar_views.py` instead.

## 2026-10-30 — Refactored `analyst.Bivar` as a `DataSet` child (breaking)
Mirrors `Univar`: `Bivar(name, alias)` + `load_data`/`set_data(x, y)`, `update()`, `_set_fields`/`get_metadata` (xunits/yunits), and the `view_specs`/`layouts`/`_get_fig_specs`/`_build_axes`/`_plot`/`view(show, return_fig)` pipeline. `view_model` folded into `view_specs["layout"] = "model"` + `view_specs["model_type"]`. Renamed `updata_model_data` → `_update_model_data`, `correlation` → `get_correlation`, `assess_error_normality` → `get_error_normality`. Model parameter names now `c0, c1, ...` to match function args, so models are evaluated with explicit kwargs. Fixed RMSE (was squared MSE). Removed broken `prediction_bands` (todo kept). Static metrics `bias/rmse/mae/rsq` unchanged (used by `hydrology/upscaled.py`). Added `tests/unit/test_analyst_Bivar.py` (9 tests, one temp CSV, figures not written to disk).

## 2026-09-15 — Added `query_sql(sql, params=None)` to `DataBase`
Accepts SQL text or `.sql` file path; returns a `pandas.DataFrame` via `pd.read_sql`. Complements `execute_sql` (write-only) with a read path for arbitrary SELECT queries. No epoch conversion applied — callers handle datetime via SQLite native functions (e.g. `datetime(col, 'unixepoch')`).

## 2026-09-15 — Added NOT NULL constraint to `records.value`
`value REAL NOT NULL` in `records.sql`. Users must fill or drop nulls and assign a flag before inserting. Only affects newly created databases.

## 2026-09-15 — Added `query_records(query_dict)` to `DataBase`
Single dict interface for extensibility; keys: start, end, flag_value, spec_id, transform_values. JOIN on specs for inverse transform; `datetime` returned as UTC-aware pandas Timestamps.

## 2026-09-15 — Added `insert_row(row_dict, on_table, columns_map=None)` to `DataBase`
Dict convenience wrapper around `insert_rows`; handles epoch conversion automatically for tables in `_EPOCH_COLS` (e.g. `specs.start/end`). Placed between `insert_rows` and `insert_records`.

## 2026-09-15 — Changed `columns_map` convention in `databases.py`
Keys are now DB column names, values are CSV column name (str) or column index (int, 0-based). Private helper `_apply_columns_map` centralises the resolution. Updated `insert_rows`, `insert_records`, and all related docstrings.

## 2026-09-15 — Added `load_records(files, spec_id, sep=None, ...)` to `DataBase`
Bulk CSV loader; reads and concatenates all files, delegates to `insert_records` with the same parameter set (spec_id, flag, columns_map, transform_values).

## 2026-09-15 — Fixed silent NaN insert bug in `databases.py:insert_records`
Added required-column validation after `columns_map` rename; raises `ValueError` with sorted list of missing columns (`datetime`, `value`, `flag_value` when `flag=None`) instead of silently inserting NULLs.

## 2026-09-15 — Finalised `databases.py` inspect methods, insert API, and large-table hardening
Renamed all inspect methods consistently: `inspect_schema`, `inspect_specs`, `inspect_records`. All three accept `quiet=False` and always return the formatted string. `inspect_schema` accepts optional `table=` filter (single table prints linearly; no arg uses 3-col layout). `inspect_records` shows human-readable timestamps via `_fmt_records`; tail query uses `DESC LIMIT` subquery instead of `OFFSET` to avoid full-table scans. `flag=None` parameter added to `insert_records`/`insert_record` to broadcast a constant `flag_value`. `insert_record` is a single-row dict convenience wrapper. Added two indexes to `records.sql`: composite `(spec_id, datetime)` and standalone `datetime`.

## 2026-09-15 — Extended `databases.py` with inspection, insert variants, and design refinements
Added `close()`, `inspect_schema()` (3-col fixed-order layout), `inspect_specs()` (card-per-spec with epoch→date display), `insert_record()` (single-row dict wrapper).
Key design decisions: `spec_id` is a parameter of `insert_records`/`insert_record`, not a DataFrame column; records seeding removed from `new()` — workflow is now two-step: `new()` creates structure + seeds catalogues/specs, then `insert_records()` for data. `new()` wraps all creation in try/except and deletes the partial file on any error. Text timestamps auto-converted to epoch via `_to_epoch` for `specs.start/end` and `records.datetime`. `overwrite=False` added to `new()`. `file_csv_sep` from `MbaE` used throughout.

## 2026-09-15 — Implemented foundational `databases.py` and populated all catalogue CSVs
Implemented `connect`, `execute_sql`, `parse_setup`, `new`, `_seed_catalog`, `insert_rows`, `insert_records` in `DataBase`.
Added `theme` column to `variables.csv`; wrote dummy `statistics.csv` (mean/sum/min/max) and `sources.csv` (CHIRPS/INMET/ANA); fixed `specs.sql` comment (formula: `stored = actual * scale + offset`).


## 2026-09-15 — Addressed all `# todo [docstring]` in `datasets/core.py`
Added docstrings to: `TimeSeries` class, `get_range_datetime`, `_build_axes`, `plot_series`, `add_hour`, `export_data` (TimeSeriesCollection), `reducer`, `mean/rng/std/min/max/percentile/percentiles/stats` (TimeSeriesSamples), `get_weights_by_name` (TimeSeriesSpatialSamples), `Raster._get_fig_specs`, `SciRaster`. Also replaced/improved class-level docstrings for `TimeSeriesSamples` and `TimeSeriesSpatialSamples`.
Note: `rng()` uses `np.r` which appears to be a bug (np.r is an array concatenator, not a range/ptp function) — flagged but not fixed.


## 2026-09-15 — Harmonised all module-level docstrings across the project
Replaced all placeholder/Lorem ipsum content with concise one-sentence goal descriptions. Policy: API modules (datasets, hydrology, parsers, tools/core, etc.) get a single descriptive sentence; standalone tool scripts (analysis_sav, analysis_spatial_normals, template) may keep fuller docstrings with usage and config details.
