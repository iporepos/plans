# Memory Log

## 2026-11-06 — Inserts validate before writing: unknown flags, unparseable dates, extra columns, and specs pointing to unknown catalogue entries (plan item 5.3), with tests in `TestInsertValidation`
`_to_epoch` raises on non-null inputs that fail to parse, instead of coercing them to `None`. Null `end` in specs stays valid. `drop_extra` is on `insert_rows`, `insert_row`, `insert_records`, `insert_record` and `load_records`.

## 2026-11-06 — Extra DataFrame columns raise on insert by default; `drop_extra=True` opts out (option c for plan item 5.3)
Silent dropping hid typos in specs files (`ofset` led to `offset = 0`) and merged grid cells when `geometry_id` was dropped on the base class. The opt-out keeps wide CSV loads through `load_records` to one argument.

## 2026-11-06 — Unit tests for plan item 5.2 added as `TestSpecNames` in `tests/unit/test_databases.py`
No soft tests from Ipo this session, so tests follow each patch directly.

## 2026-11-06 — Spec names are unique and uppercase; `spec_name` added to the insert and query methods, with `spec_id` kept as fallback (plan item 5.2)
Approved change to `data/sql/base/specs.sql`: `UNIQUE` plus a `CHECK` on the name format. Input names are stripped and uppercased (lenient lookup), and duplicates raise. Only `_resolve_spec_ids` maps names and ids, and child classes reuse it. `spec_id` now accepts numpy integers but rejects floats. `inspect_specs` shows the name first and the id after it.

## 2026-11-06 — New `tests/unit/test_databases.py` with unittest tests for plan item 5.1 (SQL lookup with fallback to `base/`)
Unittest style, like the other unit modules (pytest is not in the venv). One temp folder per class holds two databases, so few files are created.

## 2026-11-06 — `DataBase.new()` resolves each table's SQL in the subclass `SQL_DIR`, falling back to `base/`; a missing `.sql` path now raises `FileNotFoundError`
Plan item 5.1. Before, a subclass with a partial SQL folder (like `semispatial/`) failed because the missing path was run as SQL text. `execute_sql` and `query_sql` share a private `_read_sql`.

## 2026-11-06 — Databases plan: public spec parameter is `spec_name=` (preferred) with `spec_id=` kept as fallback, instead of replacing `spec_id` by `spec=`
Avoids a breaking change and follows Rule 5 naming (`variable_name`, `source_name`). A shared resolver maps either one to ids. Supersedes decision 4.1.3 of `prompts/new_features_ideas/plans_databases.md` on this point. Details: name always wins, and a conflicting id issues a warning saying the name was used; `spec_id` keeps its current position, `spec_name` comes after it; inserts raise if both are None, queries treat both None as all specs; a warning admonition in docstrings says ids are only stable inside one database file.

## 2026-11-03 — Map panel clears axis labels after drawing, since geopandas 1.2 adds them from the CRS and they fall off the figure
Found by CI, which installs the latest packages, while the local venv had geopandas 1.1.1. Clearing works on all versions, while `add_labels=False` fails on older ones.

## 2026-11-03 — Annotations of `GeoUnivar` and `Raster` move below the lateral panels and never pass the bottom of the map; the figure is shorter
`Univar.plot_text_columns` places columns of text in that box. `median` is dropped, since it repeats `p50`, and rasters show cell units and the EPSG code. `PROJ_LIB` and `GDAL_DATA` on this machine point to an old install, which degrades CRS reading, so `get_crs_info` reads units from the WKT as a fallback.

## 2026-11-03 — Color bar tips mark where `range` clips the data, with no spec; `edges_cbar` removed; data points take 1/3 of the panel in `GeoUnivar` and `Raster`
"Sharp edges" meant these tips, not lines between classes, so the lines and their spec are gone. No new dependency: `extend` in matplotlib, with the locator removed so tips do not shrink the bar.

## 2026-11-03 — Panels get one drawing order: background, raster, grid, plot elements, ticks and frame; grid of maps is nearly centered
An axis draws ticks and grid together, so `viewer.AxisGrid` draws the grid as its own artist, and `viewer.set_layers` runs at the end of every family `view`. Statistics, raster metadata, mean labels and area labels share one darker gray and are one point smaller (`viewer.get_annotation_specs`). Histograms always have three integer labels in percent. Data panels of rasters use a dynamic opacity by default.

## 2026-11-03 — Color bar of `GeoUnivar` and `Raster` moves in line with the side panels and holds their y axis
It shares `range`, so outer classes now reach the ends of the range. The data panel is narrower and has no axis labels, the map has 3 round ticks with a grid, and the default title of the data panel is "Data" in all of `Univar`.

## 2026-11-03 — `Raster` now inherits from `GeoUnivar`, with `.data` still a grid; its figures follow the family
Removes the duplicated `_plot`, `view` details and `get_univar`. Default colors are continuous for rasters and classes for points. Statistics are lazy, but `get_stats` and every view compute from the current grid, because `mask_nodata` edits float grids in place. Normality and Gumbel raise an error on `QualiRaster`. Confirmed old bugs fixed in the same pass, including `RasterCollection.reduce`, which failed at HEAD.

## 2026-11-03 — `GeoUnivar` gets a real color bar, a `continuous` scheme and `helper_geometry`, which replaces `layers_map`
The bar is a child axis of the map, so it follows the square panel and panel indexes do not change. In-panel strips and `colorize_map` gave way: strips stay as options, off by default. No new dependency: `BoundaryNorm` and `drawedges` in matplotlib give the sharp edges.

## 2026-11-03 — Raster plan: re-parent under `GeoUnivar` by stages, with `.data` kept as a grid; no Raster source changed
A runtime prototype ran all of `raster_01` with the same grids, using only `_get_values()`, `_plot_map()` and lazy statistics. This replaces the earlier advice to reuse without re-parenting. Plan and confirmed bugs in `testing/raster_geounivar_assessment.md`, decisions on map colors and `QualiRaster` getters still open.

## 2026-11-03 — Gaps tutorial shows all gaps first; `get_epochs` sees gaps at the end, `interpolate_gaps` stops extrapolating and flags only filled records
The small gaps were in the plotted data, but one hour was 0.05 pixels wide. `linewidth_gaps` keeps them visible in the `epochs` layout. The standard grid pads the last day, and these rows stayed in the last epoch and were extrapolated.

## 2026-11-02 — CI fixes: series legend no longer overlaps the panel title; `DejaVu Sans` is the fallback for Arial
From `prompt.md`. `_set_series_legend` compared widths and ignored the legend padding, so legends could overlap the title with any font. It now compares the legend left edge with the title right edge. Not confirmed on CI itself. `dropna(inplace=True)` warnings from pandas 3.1 left as they are. Raster assessment parked in `testing/raster_geounivar_assessment.md`.

## 2026-11-02 — Assessed moving `Raster` under `GeoUnivar`; no source changed, decision open
`Raster` extends `DataSet` and only borrows from `Univar`/`GeoUnivar`. The blocker is `self.data`: a grid in `Raster`, a dataframe in 13 `Univar`/`GeoUnivar` methods. Most of the reuse is available through the static `Univar.plot_*` without changing the parent. Found existing `Raster` family bugs, not fixed: `Zones()`, `load_metadata` and `load_tif_metadata` on tif, base `get_aoi`, `get_zonal_stats`, `cellsize` in `set_raster_metadata`.

## 2026-11-02 — All panels show tick labels: dates on every stacked panel, y values on histograms and CDFs
These are plots for inspecting data, so readable values come first. Axis labels stay on the last panel, and the data panel gave up one grid column to make room for the labels, keeping histogram and CDF at the same width. Long labels can still overflow, by the user's choice. The y axis title stays on the data panel only, except in Raster views, whose map has no y title, so the histogram keeps the one with the units.

## 2026-11-02 — Renamed `noise_sd` to `remainder_sd`, `season_shape` to `cycle_shape` and `season_component` to `cycle_component`
Requested by the user, no aliases kept since the code is new. The value was already the standard deviation of the remainder, not of the shocks.

## 2026-11-02 — TimeSeries fine tunings: `epochs` layout replaces `view_epochs()`, `n_dates=5`, `pad_x=0.05`, spec tables in `view()` docstrings, `decompose()`, new synthetic tutorial
From `prompt.md`. Trend, Cycle, Remainder (Memory and Shocks) and Shocks in tutorials; the `arma.decompose()` key `season` became `cycle`. `SeasonalEnsemble` has `pad_x=0`, since padding would repeat months at the edges. Thin `view()` overrides were added to hold the tables. Raster views and the `noise_sd` name were left as they are.

## 2026-11-02 — Series only change when asked: `dropnan=False` by default, reads work on a regular copy, specs survive `update()`, `tsc.standardize()` no longer fills gaps
User decisions. `update()` keeps specs the user changed, `get_epochs`/`interpolate_gaps(inplace=False)`/`update_epochs_stats` use `_get_standard_data()`. `get_epochs()` now sees missing timestamps. The fill in `tsc.standardize()` dated from the first commit, but only `regionalize()` and tutorial 07 used it, so `regionalize()` now fills small gaps from other series instead of interpolating or zeroing them.

## 2026-11-02 — Fixed: sums no longer invent zeros in gaps; `full`/`simple` views leave the series untouched; smaller plot fixes
`standardize()` and `aggregate()` use `min_count=1` for sums, so results change where gaps used to read as 0, including empty periods in `scale_up()` with default data. The Gantt views work on a deep copy. Also: `maxticks=7` for date ticks, legend drops columns to clear the panel title and panels lower to clear the figure title, repeated panel colors take the farthest color of the map, `Celsius` spelling.

## 2026-11-02 — New tutorial `timeseries_12_collection_views` on collection visuals; found gap bug in `standardize()`, not fixed
Tutorial is organized by the question each layout answers. `standardize()` turns all-NaN groups into 0 for `agg="sum"` series (pandas sum), reached with `dropnan=False` through the `full`/`simple` views; those views also reset member `view_specs`. Left for the user to decide, and the tutorial uses the default `dropnan=True`.

## 2026-11-02 — `stacked` layout now has histogram and CDF panels; series-only version is `stacked-simple`; two rows between panels
User decision. A lone series keeps the look of its own view, and series sharing a panel overlay in their own colors. The wider gap keeps each title closer to its own panel.

## 2026-11-02 — New `stacked` layout in `TimeSeriesCollection`, with `panels` and `panel_heights` specs
User decision. One layout, with the panel count from `panels`, rather than `stacked-2/3/4`. Series keep their own `view_specs`; mixed units in a panel raise. Inverted hyetographs and similar special cases go to dedicated classes later. Unknown collection layouts now raise instead of falling back to the Gantt view.

## 2026-11-02 — `GeoUnivar`: `set_data()`, `layers_map` and `n_classes_cmap` specs; `view()` no longer adds a column; `mini` gap closed
User decision. `zorder_map` default went from 0 to 3, so layers stay below points. `load_data` gets `input_varfield` and now renames that column to `varfield`, as in `Univar`. `n_classes_cmap` lives in `Univar`, so the colorized scatter follows it too.

## 2026-11-02 — `univar_03_geo` fine-tuning now compares the `scheme_cmap` options
User decision. Replaces the marker and grid example. Shows `equal` and `quantiles` with their bin edges, then `cmap`.

## 2026-11-02 — `GeoUnivar` map panel always square, at the top left of its cell
User decision. Geopandas shrank the panel to the map aspect, so it floated in its cell. Now the view limits widen instead (`adjustable="datalim"`), which also keeps layers added later in view. `mini` map moved to column 1, the same left side as `full`.

## 2026-11-02 — New tutorial `univar_03_geo`: `GeoUnivar` from scratch with points and a catchment
User decision. Source code untouched: the catchment is drawn on the map axes from `view(return_fig=True)`, since `GeoUnivar` has no setter or spec for extra layers.

## 2026-11-01 — Ensemble bands more solid: `color_band` `#8db4dc`, `alpha_band` 0.6
User decision. Keeping `tab:blue` at a higher alpha hid the highlight and mean lines, which share that blue, so the color got lighter too. A lighter color at 0.8 lost nested bands. Y range stays as is when background lines are hidden, also by user decision.

## 2026-11-01 — Ensemble layers fixed as background, bands, reducers, highlight; new `plot_background` view spec
User decision. Bands were already above background members, only translucent. The real fault was reducers drawn over highlights. `plot_background=False` hides background lines in the series panel only, and keeps the y range from all members so it stays aligned with the histogram.

## 2026-11-01 — Series legends always on top; `series-simple` panel to the figure side; new `viewer.clear_xticks`
User decision. Inward ticks stay, so `clear_xticks` lowers the y limit slightly when a y grid line would cross the x ticks. Applied in `TimeSeries.view`, the compare view and the collection series panel. `Univar` figures are not covered.

## 2026-11-01 — `TimeSeries.get_seasonal_ensemble()`, seasonal unit tests and tutorial `timeseries_11_seasonal`
User decision. Seasonal tests went into `test_datasets_TimeSeriesEnsemble.py` rather than a new test module. Inward ticks stay, deliberate for the `wien` style, so y grid lines can still cross x ticks near the bottom edge (matplotlib draws each axis grid and ticks together).

## 2026-11-01 — New `SeasonalEnsemble`: years of one series as ensemble members
User decision. Dates move onto a reference span holding a leap February, so the parent reducers and views work unchanged. `year_start` gives water years. Incomplete years stay in. Reducers return placeholder dates (option A), noted in the docstring. Steps that do not repeat each year raise `ValueError`, and monthly steps move to the first of the month. Unit tests and tutorial wait for the user's soft test.

## 2026-11-01 — `TimeSeries` panels share a y range; `GeoUnivar` limited to `full` and `mini`; stochastic tutorial uses `viewer` style
User decision. `TimeSeries.update()` keeps the parent range across its specs reset, so outliers show on every panel. `GeoUnivar` now has its own `layouts` and drops its `_get_fig_specs`, so other layouts raise `ValueError`. The tutorial uses the `wien` style, `FIG_SIZES` and the library's plain colors, since `viewer` has no palette.

## 2026-11-01 — `Univar` plotting goes through `view()` and layouts; new `qq` layout; `plot_qqplot` removed
User decision. `_plot` dispatches to `_plot_full` or `_plot_qq`, like `Bivar`, with a new static `plot_qq`. Unknown layouts now raise `ValueError` in `Univar` and `Bivar`, and `view()` raises without data. `data_plot` stays a separate key. `TimeSeries.view()` is left for a separate step: its panels do not share a y range, because the data panel and the histogram and CDF get different specs.

## 2026-11-01 — `make_synthetic_tsn` removed, without a deprecation release
User decision: the user deleted the method and its test was removed. Overrides the earlier plan of warning for one release; the warning never shipped, so callers of the pip package get an `AttributeError`.

## 2026-11-01 — `standardize()` docstring example and `timeseries_04` text match the whole-day grid
The grid pads to 23:00 on the last day, so the old 361 rows and the "full regular hourly range" wording were out of date.

## 2026-11-01 — `make_synthetic_tsn` deprecated (step 3); `view_compare_times_series` shares a y range
Requested by the user. `make_synthetic_tsn` warns with `DeprecationWarning`, for removal in the next release. The compare view drew the histogram and CDF on the second series' range, cutting off the first; it now covers both unless `specs` has `"range"`, so the `timeseries_05` workaround is gone.

## 2026-11-01 — All 7 notebooks moved from `make_synthetic_tsn` to `generate()` (step 2)
Notebooks now use the default parameters, so the column is `v` and axis ranges changed. `timeseries_07` uses child classes (columns `ppt`, `Q`, `tas`, `et`). `timeseries_05` changed from 1 month hourly to 4 years daily, because a month has too little season to compare. Stored outputs were cleared from `timeseries_03` and `timeseries_05`, because they would be stale. `make_synthetic_tsn` not deprecated yet.

## 2026-11-01 — Soft test script `testing/datasets_TimeSeries_generate.py`
Requested by the user, for `generate()` and `fit()`. The `testing/` folder is git-ignored.

## 2026-11-01 — `TimeSeries.generate()` and `fit()`, with defaults by child class (step 1 of replacing `make_synthetic_tsn`)
User decisions: `generate()` returns a DataFrame by default, and `inplace=True` sets the object data (overrides the brief's "never mutate"); no daily cycle at any step, since hourly series will come from downscaling a daily series. Child defaults live in `generator_specs` in physical terms (memory in days, peak day of year), because `phi`, `sigma`, `slope` and `phase` depend on the step; values are plausible for examples, not climatology. `fit()` measures the step from timestamps because `dtfreq` is a coarse label (3h data is labelled `h`), and rejects irregular data because `set_data` drops NaN rows, which otherwise fits silently wrong (tested: phase 11.88 vs 6). `fit()` stores `origin` and `freq`, so `generate()` can start on any date. `arma` now accepts a float `period` (daily is 365.2425). `make_synthetic_tsn` and the notebooks are untouched: migration and deprecation are the next steps.

## 2026-11-01 — Non-Gaussian noise rejected for now; rain-like example pruned at zero
User decision: keep additive Gaussian noise in `arma`, and handle positive variables downstream. A prototype compared gamma and lognormal noise (centered gamma did not prevent negatives; multiplicative lognormal did, with no extra parameters, but cannot represent exact zeros); nothing was added to the package. `stochastic_01_arma` keeps the rain-like limitation and prunes negatives with `np.clip` in the notebook only, reporting the shift in the mean.

## 2026-11-01 — `stochastic_01_arma`: autoregression scatter, y axis from zero, third phi
Requested by the user. Series plots start the y axis at zero, except the rain-like plot, where that would hide the negative values the section is about. Non-Gaussian noise is under discussion only; no package code yet.

## 2026-11-01 — New tutorial `stochastic_01_arma`
Simple showcase of `plans.stochastic.arma` with plain arrays and matplotlib, no `TimeSeries`, registered after `bivar_02_models` in `docs/examples.rst`. Includes the positive-variable limitation (rain-like series below zero) instead of claiming it stays positive, as the brief's step 6 did. Seed chosen on purpose: seed 1 gave the lowest `phi` of 300 seeds (0.325 vs true 0.5, mean 0.481), so the notebook uses a typical seed and shows the spread across seeds.

## 2026-11-01 — Golden test tolerance for curve fits (CI failure)
`test_golden` failed on CI for `fit_Power` by 6e-8 while passing locally. Not a regression: `curve_fit` stops at its solver tolerance, and locally changing only solver settings moves `Bias` by up to 8e-6. Fit cases now use `TOL_FIT` (1e-4), other golden cases keep `TOL_EXACT` (1e-8). Also noted: CI installs unpinned dependencies on Python 3.11 and already warns that pandas will remove `inplace` (PDEP-8); not changed.

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
