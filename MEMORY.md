# Memory Log

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
