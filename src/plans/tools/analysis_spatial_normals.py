# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
``analysis_spatial_normals`` -- standalone PLANS tool.

Self-contained script: copy this single file anywhere and run it with
Python 3. It has no dependency on the ``plans.tools.core`` module --
all parameters are passed through a single JSON config file.

From a monthly raster time series (e.g., NDVI), this tool builds:

1. Annual aggregations (one or more statistics per year).
2. Climatological normals -- annual and monthly, over a configurable
   horizon.
3. Anomalies -- monthly and annual, absolute and relative/percent.

Assumes all input rasters share the same grid (shape, transform, CRS),
and that monthly raster filenames end with a fixed ``"_<YYYY>_<MM>"``
suffix before the extension, month zero-padded, e.g. ``NDVI_2020_01.tif``.
The only third-party dependencies are ``numpy`` and ``rasterio``.

Usage
-----

.. code-block:: bash

    python analysis_spatial_normals.py --config config.json

Config file
-----------

The ``--config``/``-c`` flag points to a JSON file. Template, ready to
copy and paste:

.. code-block:: json

    {
      "input": "data/ndvi_monthly",
      "output": "output/run1",
      "label": "ndvi_normals_v1",

      "pattern": "*.tif",
      "verbose": true,
      "annual": {
        "stats": ["mean", "sum", "max", "p90"],
        "min_months": 12
      },
      "normals": {
        "stats": ["mean", "std"],
        "annual_base_stat": "mean",
        "annual_horizon": [2000, 2020],
        "monthly_horizon": null
      },
      "anomalies": {
        "monthly": true,
        "annual": true,
        "relative": true
      },
      "styles": {
        "annual": "styles/annual.qml",
        "annual_normal": "styles/annual_normal.qml",
        "monthly_normal": "styles/monthly_normal.qml",
        "anomaly_absolute": "styles/anomaly_absolute.qml",
        "anomaly_relative": "styles/anomaly_relative.qml"
      }
    }

Required fields
~~~~~~~~~~~~~~~~
* ``input`` (str) -- folder containing the monthly raster files.
* ``output`` (str) -- output folder for run artifacts.
* ``label`` (str) -- run label, used as the logger name.

Optional fields
~~~~~~~~~~~~~~~~
* ``pattern`` (str, default ``"*.tif"``) -- glob pattern for input files.
* ``verbose`` (bool, default ``false``) -- echo logs to console.
* ``annual`` (dict, default ``{}``) -- see :func:`aggregate_annual`; keys
  ``stats`` (list[str], default ``["mean"]``) and ``min_months`` (int,
  default ``12``).
* ``normals`` (dict, default ``{}``) -- see :func:`compute_annual_normals`
  / :func:`compute_monthly_normals`; keys ``stats`` (list[str], default
  ``["mean"]``), ``annual_base_stat`` (str, default ``"mean"``),
  ``annual_horizon`` and ``monthly_horizon`` (``[start_year, end_year]``
  or ``null``, default ``null``).
* ``anomalies`` (dict, default ``{}``) -- see
  :func:`compute_monthly_anomalies` / :func:`compute_annual_anomalies`;
  keys ``monthly`` and ``annual`` (bool, default ``true``), ``relative``
  (bool, default ``true``).
* ``styles`` (dict, default ``{}``) -- see :func:`apply_style`. Each key
  is optional; when present, its value is a path to a QGIS ``.qml`` style
  template that gets copied as a same-named sidecar next to every raster
  in that output category, so QGIS auto-applies it on load. Keys:
  ``annual`` (the per-year aggregates), ``annual_normal``,
  ``monthly_normal``, ``anomaly_absolute`` (used for both monthly and
  annual absolute anomalies), and ``anomaly_relative`` (ditto, relative
  anomalies).

The ``REQUIRED``/``OPTIONAL`` dictionaries just below are the actual
validation source of truth for the top-level fields -- keep them in sync
with this docstring whenever you add, rename or remove a field. Nested
sub-dict defaults (``annual``, ``normals``, ``anomalies``) are filled in
by :func:`process_data`.
"""

# IMPORTS
# ***********************************************************************
import argparse
import json
import logging
import re
import shutil
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import rasterio


# CONFIG SCHEMA
# ***********************************************************************
# Required fields: {name: type}
REQUIRED = {
    "input": str,
    "output": str,
    "label": str,
}
# Optional fields: {name: (type, default)}
OPTIONAL = {
    "pattern": (str, "*.tif"),
    "verbose": (bool, False),
    "annual": (dict, None),
    "normals": (dict, None),
    "anomalies": (dict, None),
    "styles": (dict, None),
}


def load_config(file_config):
    """Load, validate and fill defaults for the JSON config file.

    Checks that every key in :data:`REQUIRED` is present and of the
    right type, then fills in defaults for any missing key in
    :data:`OPTIONAL` and type-checks those that were provided.

    :param file_config: path to the JSON config file.
    :type file_config: str or pathlib.Path
    :return: validated configuration dictionary, defaults included.
    :rtype: dict
    :raises ValueError: if a required field is missing, or any field
        has the wrong type.
    """
    cfg = json.loads(Path(file_config).read_text())

    missing = [k for k in REQUIRED if k not in cfg]
    if missing:
        raise ValueError(f"Missing required config field(s): {missing}")

    for k, t in REQUIRED.items():
        if not isinstance(cfg[k], t):
            raise ValueError(
                f"Config field '{k}' must be {t.__name__}, got {type(cfg[k]).__name__}"
            )

    for k, (t, default) in OPTIONAL.items():
        cfg.setdefault(k, default)
        if cfg[k] is not None and not isinstance(cfg[k], t):
            raise ValueError(
                f"Config field '{k}' must be {t.__name__}, got {type(cfg[k]).__name__}"
            )

    return cfg


def get_logger(name, log_file, talk=True):
    """Create a simple console + file logger.

    :param name: logger name, shown in every log line.
    :type name: str
    :param log_file: path to the log file to write to.
    :type log_file: str or pathlib.Path
    :param talk: whether to also emit log records to the console.
    :type talk: bool
    :return: configured logger instance.
    :rtype: logging.Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if logger.hasHandlers():
        logger.handlers.clear()

    fmt = logging.Formatter(
        fmt=f"%(asctime)s.%(msecs)03d | %(levelname)-8s | {name} >>> %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if talk:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(fmt)
        logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, mode="w")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger


# DATA STRUCTURES
# ***********************************************************************


@dataclass
class MonthlyRaster:
    """Reference to a single monthly raster file.

    :param year: Calendar year, e.g. ``2020``.
    :type year: int
    :param month: Calendar month, ``1``-``12``.
    :type month: int
    :param path: Path to the raster file on disk.
    :type path: str
    """

    year: int
    month: int
    path: str


# STAT HELPERS
# ***********************************************************************

# Fixed filename convention: "..._<YYYY>_<MM>.<ext>"
_DATE_SUFFIX_RE = re.compile(r"_(\d{4})_(\d{2})(?=\.[A-Za-z0-9]+$)")

_BASE_STAT_FUNCS: dict[str, Callable] = {
    "mean": np.nanmean,
    "sum": np.nansum,
    "max": np.nanmax,
    "min": np.nanmin,
    "median": np.nanmedian,
    "std": np.nanstd,
}
_PCT_RE = re.compile(r"^p(\d{1,3})$")


def _resolve_stat_func(stat: str) -> Callable:
    """Resolve a stat name to a NaN-aware ``(array, axis) -> array`` reducer.

    :param stat: Statistic name. One of the keys in ``_BASE_STAT_FUNCS``
        (``"mean"``, ``"sum"``, ``"max"``, ``"min"``, ``"median"``, ``"std"``),
        or ``"pN"`` for the Nth percentile, e.g. ``"p10"``, ``"p90"``.
    :type stat: str
    :returns: A reducer function usable as ``func(stack, axis=0)``.
    :rtype: callable
    :raises ValueError: If ``stat`` is not a recognized name, or a percentile
        is outside the 0-100 range.
    """
    if stat in _BASE_STAT_FUNCS:
        return _BASE_STAT_FUNCS[stat]
    m = _PCT_RE.match(stat)
    if m:
        q = int(m.group(1))
        if not (0 <= q <= 100):
            raise ValueError(f"Percentile stat '{stat}' out of range 0-100")
        return lambda arr, axis: np.nanpercentile(arr, q, axis=axis)
    raise ValueError(
        f"Unknown stat '{stat}'. Use one of {list(_BASE_STAT_FUNCS)} or 'pN' for the Nth percentile."
    )


# DISCOVERY / PARSING
# ***********************************************************************


def parse_monthly_rasters(
    folder, logger, pattern: str = "*.tif"
) -> list[MonthlyRaster]:
    """Scan a folder for monthly rasters following the fixed naming convention.

    Files must end with a ``"_<YYYY>_<MM>"`` suffix before the extension,
    month zero-padded, e.g. ``NDVI_2020_01.tif``.

    :param folder: Directory to scan.
    :type folder: str or pathlib.Path
    :param logger: Logger instance for warnings about unmatched filenames.
    :type logger: logging.Logger
    :param pattern: Glob pattern used to list candidate files.
    :type pattern: str
    :returns: Parsed monthly rasters, sorted chronologically.
    :rtype: list[MonthlyRaster]
    """
    files = sorted(Path(folder).glob(pattern))
    records = []
    for f in files:
        m = _DATE_SUFFIX_RE.search(f.name)
        if not m:
            logger.warning(
                f"filename does not match '_YYYY_MM' suffix convention, skipped: {f}"
            )
            continue
        year, month = int(m.group(1)), int(m.group(2))
        records.append(MonthlyRaster(year=year, month=month, path=str(f)))
    records.sort(key=lambda r: (r.year, r.month))
    return records


def validate_grid_consistency(paths: list[str], logger) -> None:
    """Check that a set of rasters share the same grid.

    :param paths: Raster file paths to compare.
    :type paths: list[str]
    :param logger: Logger instance for a confirmation message.
    :type logger: logging.Logger
    :returns: None
    :rtype: None
    :raises ValueError: If any raster's width, height, transform, or CRS
        differs from the first raster's.
    """
    ref = None
    ref_path = None
    for p in paths:
        with rasterio.open(p) as src:
            key = (src.width, src.height, src.transform, src.crs)
        if ref is None:
            ref, ref_path = key, p
        elif key != ref:
            raise ValueError(
                f"Grid mismatch: '{p}' does not match reference grid '{ref_path}'"
            )
    logger.debug(f"grid consistency OK across {len(paths)} raster(s)")


# RASTER I/O HELPERS
# ***********************************************************************


def _read_as_float(path) -> tuple[np.ndarray, dict]:
    """Read band 1 of a raster as float64, converting nodata to NaN.

    :param path: Path to the raster file.
    :type path: str or pathlib.Path
    :returns: A 2-tuple of the pixel array and the rasterio profile.
    :rtype: tuple[numpy.ndarray, dict]
    """
    with rasterio.open(path) as src:
        profile = src.profile
        arr = src.read(1).astype("float64")
        nodata = src.nodata
        if nodata is not None and not np.isnan(nodata):
            arr[arr == nodata] = np.nan
    return arr, profile


def _write_raster(arr: np.ndarray, profile: dict, out_path) -> None:
    """Write a single-band float32 raster with NaN nodata.

    :param arr: Pixel array to write.
    :type arr: numpy.ndarray
    :param profile: Rasterio profile to reuse (CRS, transform, etc.); its
        ``dtype``, ``count``, and ``nodata`` are overridden.
    :type profile: dict
    :param out_path: Output file path; parent directories are created if needed.
    :type out_path: str or pathlib.Path
    :returns: None
    :rtype: None
    """
    out_profile = profile.copy()
    out_profile.update(dtype="float32", count=1, nodata=np.nan)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out_path, "w", **out_profile) as dst:
        dst.write(arr.astype("float32"), 1)


def _apply_stat(stack: np.ndarray, func: Callable) -> np.ndarray:
    """Apply a stat reducer across axis 0 of a stack.

    Silences the expected "all-NaN slice" warning for pixels that are
    nodata in every layer of the stack (those pixels correctly come out
    as NaN in the result).

    :param stack: Array stacked along axis 0 (e.g. one layer per month or year).
    :type stack: numpy.ndarray
    :param func: Reducer called as ``func(stack, axis=0)``.
    :type func: callable
    :returns: The reduced array.
    :rtype: numpy.ndarray
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        return func(stack, axis=0)


def _read_stack(records: list[MonthlyRaster]) -> tuple[np.ndarray, dict]:
    """Read a list of rasters into a single stacked array.

    :param records: Rasters to read, in the order they should be stacked.
    :type records: list[MonthlyRaster]
    :returns: A 2-tuple of the stacked array (axis 0 = record index) and the
        rasterio profile of the first record.
    :rtype: tuple[numpy.ndarray, dict]
    """
    arrays, profile = [], None
    for r in records:
        arr, prof = _read_as_float(r.path)
        arrays.append(arr)
        if profile is None:
            profile = prof
    return np.stack(arrays, axis=0), profile


# PIPELINE STEPS -- annual aggregation, normals, anomalies
# ***********************************************************************


def aggregate_annual(
    monthly_rasters: list[MonthlyRaster],
    output_dir,
    logger,
    stats: list[str] = ("mean",),
    min_months: int = 12,
    file_prefix: str = "annual",
) -> dict[str, dict[int, str]]:
    """Aggregate monthly rasters into one raster per year, per requested stat.

    :param monthly_rasters: Parsed monthly rasters, as returned by
        :func:`parse_monthly_rasters`.
    :type monthly_rasters: list[MonthlyRaster]
    :param output_dir: Directory to write ``<file_prefix>_<stat>_<year>.tif``
        files into.
    :type output_dir: str or pathlib.Path
    :param logger: Logger instance for progress messages.
    :type logger: logging.Logger
    :param stats: Statistics to compute per year. See
        :func:`_resolve_stat_func` for accepted names.
    :type stats: list[str]
    :param min_months: Minimum number of valid months required for a year to
        be aggregated; years with fewer are skipped (with a warning).
    :type min_months: int
    :param file_prefix: Output filename prefix.
    :type file_prefix: str
    :returns: Mapping of ``{stat: {year: output_path}}``.
    :rtype: dict[str, dict[int, str]]
    """
    output_dir = Path(output_dir)
    by_year: dict[int, list[MonthlyRaster]] = {}
    for r in monthly_rasters:
        by_year.setdefault(r.year, []).append(r)

    output_paths: dict[str, dict[int, str]] = {s: {} for s in stats}
    for year, recs in sorted(by_year.items()):
        if len(recs) < min_months:
            logger.warning(
                f"year {year}: only {len(recs)} month(s) available (< {min_months}), skipped"
            )
            continue

        recs_sorted = sorted(recs, key=lambda x: x.month)
        stack, profile = _read_stack(recs_sorted)

        for stat in stats:
            func = _resolve_stat_func(stat)
            result = _apply_stat(stack, func)
            out_path = output_dir / f"{file_prefix}_{stat}_{year}.tif"
            _write_raster(result, profile, out_path)
            output_paths[stat][year] = str(out_path)

        logger.info(f"annual {year}: stats={list(stats)} (n={len(recs)} months)")

    return output_paths


def compute_annual_normals(
    annual_paths_by_stat: dict[str, dict[int, str]],
    output_dir,
    logger,
    base_stat: str = "mean",
    stats: list[str] = ("mean",),
    horizon: Optional[tuple[int, int]] = None,
    file_prefix: str = "annual_normal",
) -> dict[str, str]:
    """Compute annual normals from a per-year annual series.

    For the annual series identified by ``base_stat`` (e.g. the per-year
    ``"mean"`` rasters from :func:`aggregate_annual`), compute each stat in
    ``stats`` across the years within ``horizon``.

    :param annual_paths_by_stat: Per-year annual rasters, as returned by
        :func:`aggregate_annual`.
    :type annual_paths_by_stat: dict[str, dict[int, str]]
    :param output_dir: Directory to write ``<file_prefix>_<stat>.tif`` files into.
    :type output_dir: str or pathlib.Path
    :param logger: Logger instance for progress messages.
    :type logger: logging.Logger
    :param base_stat: Which annual series in ``annual_paths_by_stat`` to use
        as input.
    :type base_stat: str
    :param stats: Statistics to compute across years. See
        :func:`_resolve_stat_func` for accepted names.
    :type stats: list[str]
    :param horizon: Inclusive ``(start_year, end_year)`` window; ``None`` uses
        every available year.
    :type horizon: tuple[int, int] or None
    :param file_prefix: Output filename prefix.
    :type file_prefix: str
    :returns: Mapping of ``{stat: output_path}``.
    :rtype: dict[str, str]
    :raises ValueError: If ``base_stat`` was not computed in
        ``annual_paths_by_stat``, or no years fall within ``horizon``.
    """
    output_dir = Path(output_dir)
    if base_stat not in annual_paths_by_stat:
        msg = (
            f"base_stat '{base_stat}' was not computed in the annual step "
            f"(available: {list(annual_paths_by_stat)})"
        )
        logger.error(msg)
        raise ValueError(msg)

    series = annual_paths_by_stat[base_stat]
    years = sorted(series.keys())
    if horizon:
        start, end = horizon
        years = [y for y in years if start <= y <= end]
    if not years:
        msg = "No years available within the given annual horizon."
        logger.error(msg)
        raise ValueError(msg)

    recs = [MonthlyRaster(year=y, month=0, path=series[y]) for y in years]
    stack, profile = _read_stack(recs)

    output_paths = {}
    for stat in stats:
        func = _resolve_stat_func(stat)
        result = _apply_stat(stack, func)
        out_path = output_dir / f"{file_prefix}_{stat}.tif"
        _write_raster(result, profile, out_path)
        output_paths[stat] = str(out_path)

    logger.info(
        f"annual normals from '{base_stat}' series "
        f"({years[0]}-{years[-1]}, n={len(years)} years): stats={list(stats)}"
    )
    return output_paths


def compute_monthly_normals(
    monthly_rasters: list[MonthlyRaster],
    output_dir,
    logger,
    stats: list[str] = ("mean",),
    horizon: Optional[tuple[int, int]] = None,
    file_prefix: str = "normal_month",
) -> dict[str, dict[int, str]]:
    """Compute monthly (calendar-month) climatological normals.

    For each calendar month (1-12), compute each stat in ``stats`` across the
    years within ``horizon``. ``horizon`` is independent of the horizon used
    for the annual normals.

    :param monthly_rasters: Parsed monthly rasters, as returned by
        :func:`parse_monthly_rasters`.
    :type monthly_rasters: list[MonthlyRaster]
    :param output_dir: Directory to write ``<file_prefix>_<MM>_<stat>.tif``
        files into.
    :type output_dir: str or pathlib.Path
    :param logger: Logger instance for progress messages.
    :type logger: logging.Logger
    :param stats: Statistics to compute per calendar month. See
        :func:`_resolve_stat_func` for accepted names.
    :type stats: list[str]
    :param horizon: Inclusive ``(start_year, end_year)`` window; ``None`` uses
        every available year.
    :type horizon: tuple[int, int] or None
    :param file_prefix: Output filename prefix.
    :type file_prefix: str
    :returns: Mapping of ``{stat: {month: output_path}}``.
    :rtype: dict[str, dict[int, str]]
    """
    output_dir = Path(output_dir)
    recs = monthly_rasters
    if horizon:
        start, end = horizon
        recs = [r for r in recs if start <= r.year <= end]

    by_month: dict[int, list[MonthlyRaster]] = {}
    for r in recs:
        by_month.setdefault(r.month, []).append(r)

    output_paths: dict[str, dict[int, str]] = {s: {} for s in stats}
    for month in range(1, 13):
        month_recs = by_month.get(month, [])
        if not month_recs:
            logger.warning(f"month {month:02d}: no data in horizon, skipped")
            continue

        stack, profile = _read_stack(month_recs)

        for stat in stats:
            func = _resolve_stat_func(stat)
            result = _apply_stat(stack, func)
            out_path = output_dir / f"{file_prefix}_{month:02d}_{stat}.tif"
            _write_raster(result, profile, out_path)
            output_paths[stat][month] = str(out_path)

        logger.info(
            f"month {month:02d} normals (n={len(month_recs)} years): stats={list(stats)}"
        )

    return output_paths


def compute_monthly_anomalies(
    monthly_rasters: list[MonthlyRaster],
    monthly_normal_paths_by_stat: dict[str, dict[int, str]],
    output_dir,
    logger,
    relative: bool = True,
    normal_stat: str = "mean",
) -> dict[str, dict[tuple[int, int], str]]:
    """Compute per-month anomalies against the calendar-month normal.

    For every monthly raster, computes::

        anomaly          = value - normal[month]
        relative_anomaly = (value - normal[month]) / normal[month] * 100   # percent

    where ``normal`` is the ``normal_stat`` monthly normal (``"mean"`` by
    default -- anomalies are conventionally defined relative to the mean).
    Pixels where the normal is exactly 0 get ``NaN`` for the relative anomaly
    (percent deviation is undefined there) but still get a valid absolute
    anomaly -- relevant for variables like precipitation with dry-season zeros.

    :param monthly_rasters: Parsed monthly rasters, as returned by
        :func:`parse_monthly_rasters`.
    :type monthly_rasters: list[MonthlyRaster]
    :param monthly_normal_paths_by_stat: Monthly normals, as returned by
        :func:`compute_monthly_normals`.
    :type monthly_normal_paths_by_stat: dict[str, dict[int, str]]
    :param output_dir: Base directory; ``absolute/`` and ``relative/``
        subdirectories are created under it.
    :type output_dir: str or pathlib.Path
    :param logger: Logger instance for progress messages.
    :type logger: logging.Logger
    :param relative: Whether to also compute the percent anomaly.
    :type relative: bool
    :param normal_stat: Which monthly normal stat to use as the baseline.
    :type normal_stat: str
    :returns: ``{"absolute": {(year, month): path}, "relative": {(year, month): path}}``.
    :rtype: dict[str, dict[tuple[int, int], str]]
    :raises ValueError: If ``normal_stat`` was not computed in
        ``monthly_normal_paths_by_stat``.
    """
    output_dir = Path(output_dir)
    if normal_stat not in monthly_normal_paths_by_stat:
        msg = (
            f"normal_stat '{normal_stat}' not found among computed monthly normal stats "
            f"(available: {list(monthly_normal_paths_by_stat)})"
        )
        logger.error(msg)
        raise ValueError(msg)

    normal_by_month = monthly_normal_paths_by_stat[normal_stat]
    normal_arrays: dict[int, np.ndarray] = {}
    for month, path in normal_by_month.items():
        arr, _ = _read_as_float(path)
        normal_arrays[month] = arr

    abs_dir = output_dir / "absolute"
    rel_dir = output_dir / "relative"

    abs_paths: dict[tuple[int, int], str] = {}
    rel_paths: dict[tuple[int, int], str] = {}

    for r in monthly_rasters:
        normal_arr = normal_arrays.get(r.month)
        if normal_arr is None:
            logger.warning(
                f"no '{normal_stat}' normal for month {r.month:02d}, "
                f"skipping anomaly for {r.year}-{r.month:02d}"
            )
            continue

        arr, profile = _read_as_float(r.path)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            anomaly = arr - normal_arr

        out_path = abs_dir / f"anomaly_{r.year}_{r.month:02d}.tif"
        _write_raster(anomaly, profile, out_path)
        abs_paths[(r.year, r.month)] = str(out_path)

        if relative:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                rel_anomaly = (anomaly / normal_arr) * 100.0
                rel_anomaly = np.where(normal_arr == 0, np.nan, rel_anomaly)
            out_path_rel = rel_dir / f"anomaly_pct_{r.year}_{r.month:02d}.tif"
            _write_raster(rel_anomaly, profile, out_path_rel)
            rel_paths[(r.year, r.month)] = str(out_path_rel)

    logger.info(
        f"anomalies computed for {len(abs_paths)} monthly raster(s) "
        f"(relative={'yes' if relative else 'no'}), baseline stat='{normal_stat}'"
    )

    return {"absolute": abs_paths, "relative": rel_paths}


def compute_annual_anomalies(
    annual_paths_by_stat: dict[str, dict[int, str]],
    annual_normal_paths_by_stat: dict[str, str],
    output_dir,
    logger,
    base_stat: str = "mean",
    relative: bool = True,
) -> dict[str, dict[int, str]]:
    """Compute per-year anomalies against the mean annual normal.

    For every year in the annual series identified by ``base_stat`` (e.g. the
    per-year ``"sum"`` rasters from :func:`aggregate_annual`, for a total like
    annual precipitation), computes::

        anomaly          = annual_value[year] - annual_normal_mean
        relative_anomaly = (annual_value[year] - annual_normal_mean) / annual_normal_mean * 100   # percent

    The baseline is always the ``"mean"`` entry of ``annual_normal_paths_by_stat``,
    matching the convention used for the monthly anomalies.

    :param annual_paths_by_stat: Per-year annual rasters, as returned by
        :func:`aggregate_annual`.
    :type annual_paths_by_stat: dict[str, dict[int, str]]
    :param annual_normal_paths_by_stat: Annual normals, as returned by
        :func:`compute_annual_normals`; must include a ``"mean"`` entry.
    :type annual_normal_paths_by_stat: dict[str, str]
    :param output_dir: Base directory; ``absolute/`` and ``relative/``
        subdirectories are created under it.
    :type output_dir: str or pathlib.Path
    :param logger: Logger instance for progress messages.
    :type logger: logging.Logger
    :param base_stat: Which annual series in ``annual_paths_by_stat`` to
        compute anomalies for.
    :type base_stat: str
    :param relative: Whether to also compute the percent anomaly.
    :type relative: bool
    :returns: ``{"absolute": {year: path}, "relative": {year: path}}``.
    :rtype: dict[str, dict[int, str]]
    :raises ValueError: If ``base_stat`` was not computed in
        ``annual_paths_by_stat``, or the ``"mean"`` annual normal is missing.
    """
    output_dir = Path(output_dir)
    if base_stat not in annual_paths_by_stat:
        msg = (
            f"base_stat '{base_stat}' was not computed in the annual step "
            f"(available: {list(annual_paths_by_stat)})"
        )
        logger.error(msg)
        raise ValueError(msg)
    if "mean" not in annual_normal_paths_by_stat:
        msg = (
            f"annual normal 'mean' was not computed (available: {list(annual_normal_paths_by_stat)}); "
            f"annual anomalies always need the mean annual normal"
        )
        logger.error(msg)
        raise ValueError(msg)

    normal_arr, _ = _read_as_float(annual_normal_paths_by_stat["mean"])
    series = annual_paths_by_stat[base_stat]

    abs_dir = output_dir / "absolute"
    rel_dir = output_dir / "relative"

    abs_paths: dict[int, str] = {}
    rel_paths: dict[int, str] = {}

    for year, path in sorted(series.items()):
        arr, profile = _read_as_float(path)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            anomaly = arr - normal_arr

        out_path = abs_dir / f"anomaly_{year}.tif"
        _write_raster(anomaly, profile, out_path)
        abs_paths[year] = str(out_path)

        if relative:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                rel_anomaly = (anomaly / normal_arr) * 100.0
                rel_anomaly = np.where(normal_arr == 0, np.nan, rel_anomaly)
            out_path_rel = rel_dir / f"anomaly_pct_{year}.tif"
            _write_raster(rel_anomaly, profile, out_path_rel)
            rel_paths[year] = str(out_path_rel)

    logger.info(
        f"annual anomalies computed for {len(abs_paths)} year(s) "
        f"(relative={'yes' if relative else 'no'}), baseline='mean' of '{base_stat}' series"
    )

    return {"absolute": abs_paths, "relative": rel_paths}


# STYLING -- QGIS .qml sidecar files
# ***********************************************************************


def _iter_paths(obj):
    """Recursively yield every path string found in a nested dict/list structure.

    Walks arbitrarily nested dicts and lists/tuples (matching the shapes
    returned by :func:`aggregate_annual`, :func:`compute_annual_normals`,
    :func:`compute_monthly_normals`, :func:`compute_monthly_anomalies`, and
    :func:`compute_annual_anomalies`) and yields every string value found.

    :param obj: nested paths structure.
    :type obj: dict or list or tuple or str
    :yields: each path string found.
    :rtype: collections.abc.Iterator[str]
    """
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_paths(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _iter_paths(v)
    elif isinstance(obj, str):
        yield obj


def apply_style(paths_obj, template_path, logger) -> list[str]:
    """Copy a QGIS ``.qml`` style template as a same-named sidecar for each raster.

    For every raster path found in ``paths_obj`` (any nesting of dict/list,
    as returned by the pipeline step functions), copies ``template_path`` to
    ``<raster>.qml`` -- i.e. the raster's filename with its extension
    replaced by ``.qml`` -- so QGIS auto-applies the style when the raster
    is added to the map.

    :param paths_obj: nested output-paths structure to style.
    :type paths_obj: dict
    :param template_path: path to the ``.qml`` style template to copy.
    :type template_path: str or pathlib.Path
    :param logger: logger instance for progress messages.
    :type logger: logging.Logger
    :returns: paths of the created ``.qml`` sidecar files.
    :rtype: list[str]
    :raises FileNotFoundError: if ``template_path`` does not exist.
    """
    template_path = Path(template_path)
    if not template_path.is_file():
        msg = f"Style template not found: '{template_path}'"
        logger.error(msg)
        raise FileNotFoundError(msg)

    written = []
    for raster_path in _iter_paths(paths_obj):
        qml_path = Path(raster_path).with_suffix(".qml")
        shutil.copyfile(template_path, qml_path)
        written.append(str(qml_path))

    logger.info(f"applied style '{template_path.name}' to {len(written)} raster(s)")
    return written


def _maybe_apply_style(paths_obj, template_path, logger) -> None:
    """Call :func:`apply_style` only if ``template_path`` is truthy.

    Small convenience wrapper so callers can pass ``styles_cfg.get(key)``
    (which is ``None`` for an unconfigured style) without an ``if`` at
    every call site.

    :param paths_obj: nested output-paths structure to style.
    :type paths_obj: dict
    :param template_path: path to the ``.qml`` style template, or ``None``
        to skip styling.
    :type template_path: str or pathlib.Path or None
    :param logger: logger instance for progress messages.
    :type logger: logging.Logger
    :returns: None
    :rtype: None
    """
    if template_path:
        apply_style(paths_obj, template_path, logger)


# TOOL STEPS -- load -> process -> export
# ***********************************************************************


def load_data(cfg, logger):
    """Scan and validate the monthly raster time series described by ``cfg``.

    :param cfg: validated configuration dictionary from :func:`load_config`.
    :type cfg: dict
    :param logger: logger instance for progress messages.
    :type logger: logging.Logger
    :return: parsed monthly rasters, sorted chronologically.
    :rtype: list[MonthlyRaster]
    :raises ValueError: if no monthly rasters are found in ``cfg["input"]``.
    """
    logger.info("scanning input folder for monthly rasters")
    monthly = parse_monthly_rasters(cfg["input"], logger, pattern=cfg["pattern"])
    if not monthly:
        msg = f"No monthly rasters found in '{cfg['input']}' matching pattern '{cfg['pattern']}'"
        logger.error(msg)
        raise ValueError(msg)

    validate_grid_consistency([r.path for r in monthly], logger)
    logger.info(
        f"found {len(monthly)} monthly rasters "
        f"({monthly[0].year}-{monthly[0].month:02d} to {monthly[-1].year}-{monthly[-1].month:02d})"
    )
    return monthly


def process_data(loaded, cfg, logger):
    """Run annual aggregation, climatological normals, and anomalies.

    :param loaded: monthly rasters, as returned by :func:`load_data`.
    :type loaded: list[MonthlyRaster]
    :param cfg: validated configuration dictionary from :func:`load_config`.
    :type cfg: dict
    :param logger: logger instance for progress messages.
    :type logger: logging.Logger
    :return: dict with keys ``"annual"``, ``"annual_normals"``,
        ``"monthly_normals"``, ``"annual_anomalies"``, and
        ``"monthly_anomalies"``, holding the structures returned by
        :func:`aggregate_annual`, :func:`compute_annual_normals`,
        :func:`compute_monthly_normals`, :func:`compute_annual_anomalies`,
        and :func:`compute_monthly_anomalies` respectively. The two
        anomaly entries are ``None`` if disabled in the config. If
        ``cfg["styles"]`` has entries, :func:`apply_style` is also called
        for each configured category as a side effect (writing ``.qml``
        sidecars next to the relevant rasters).
    :rtype: dict
    """
    monthly = loaded
    output_dir = Path(cfg["output"])

    annual_cfg = cfg.get("annual") or {}
    annual_stats = list(annual_cfg.get("stats", ["mean"]))
    min_months = annual_cfg.get("min_months", 12)

    normals_cfg = cfg.get("normals") or {}
    normal_stats = list(normals_cfg.get("stats", ["mean"]))
    annual_base_stat = normals_cfg.get("annual_base_stat", "mean")
    annual_horizon = normals_cfg.get("annual_horizon")
    monthly_horizon = normals_cfg.get("monthly_horizon")
    annual_horizon = tuple(annual_horizon) if annual_horizon else None
    monthly_horizon = tuple(monthly_horizon) if monthly_horizon else None

    anomalies_cfg = cfg.get("anomalies") or {}
    anomalies_monthly_enabled = anomalies_cfg.get("monthly", True)
    anomalies_annual_enabled = anomalies_cfg.get("annual", True)
    anomalies_relative = anomalies_cfg.get("relative", True)

    styles_cfg = cfg.get("styles") or {}

    if annual_base_stat not in annual_stats:
        annual_stats.append(annual_base_stat)
        logger.info(
            f"adding '{annual_base_stat}' to annual.stats (required as normals.annual_base_stat)"
        )

    if (
        anomalies_monthly_enabled or anomalies_annual_enabled
    ) and "mean" not in normal_stats:
        normal_stats.append("mean")
        logger.info(
            "adding 'mean' to normals.stats (anomalies are always computed against the mean normal)"
        )

    annual_paths = aggregate_annual(
        monthly,
        output_dir / "annual",
        logger,
        stats=annual_stats,
        min_months=min_months,
    )
    _maybe_apply_style(annual_paths, styles_cfg.get("annual"), logger)

    annual_normal_paths = compute_annual_normals(
        annual_paths,
        output_dir / "normals" / "annual",
        logger,
        base_stat=annual_base_stat,
        stats=normal_stats,
        horizon=annual_horizon,
    )
    _maybe_apply_style(annual_normal_paths, styles_cfg.get("annual_normal"), logger)

    annual_anomaly_paths = None
    if anomalies_annual_enabled:
        annual_anomaly_paths = compute_annual_anomalies(
            annual_paths,
            annual_normal_paths,
            output_dir / "anomalies" / "annual",
            logger,
            base_stat=annual_base_stat,
            relative=anomalies_relative,
        )
        _maybe_apply_style(
            annual_anomaly_paths["absolute"], styles_cfg.get("anomaly_absolute"), logger
        )
        if anomalies_relative:
            _maybe_apply_style(
                annual_anomaly_paths["relative"],
                styles_cfg.get("anomaly_relative"),
                logger,
            )

    monthly_normal_paths = compute_monthly_normals(
        monthly,
        output_dir / "normals" / "monthly",
        logger,
        stats=normal_stats,
        horizon=monthly_horizon,
    )
    _maybe_apply_style(monthly_normal_paths, styles_cfg.get("monthly_normal"), logger)

    monthly_anomaly_paths = None
    if anomalies_monthly_enabled:
        monthly_anomaly_paths = compute_monthly_anomalies(
            monthly,
            monthly_normal_paths,
            output_dir / "anomalies" / "monthly",
            logger,
            relative=anomalies_relative,
            normal_stat="mean",
        )
        _maybe_apply_style(
            monthly_anomaly_paths["absolute"],
            styles_cfg.get("anomaly_absolute"),
            logger,
        )
        if anomalies_relative:
            _maybe_apply_style(
                monthly_anomaly_paths["relative"],
                styles_cfg.get("anomaly_relative"),
                logger,
            )

    return {
        "annual": annual_paths,
        "annual_normals": annual_normal_paths,
        "monthly_normals": monthly_normal_paths,
        "annual_anomalies": annual_anomaly_paths,
        "monthly_anomalies": monthly_anomaly_paths,
    }


def _manifest_safe(obj):
    """Recursively convert a ``processed`` results structure into a JSON-safe form.

    ``(year, month)`` tuple keys become ``"YYYY-MM"`` strings; everything
    else is passed through unchanged.

    :param obj: value to convert (dict, list/tuple, or scalar).
    :type obj: object
    :return: JSON-serializable equivalent.
    :rtype: object
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            key = (
                f"{k[0]}-{k[1]:02d}" if isinstance(k, tuple) and len(k) == 2 else str(k)
            )
            out[key] = _manifest_safe(v)
        return out
    if isinstance(obj, (list, tuple)):
        return [_manifest_safe(v) for v in obj]
    return obj


def export_data(processed, cfg, logger):
    """Write a JSON manifest listing every raster produced by the run.

    :param processed: data returned by :func:`process_data`.
    :type processed: dict
    :param cfg: validated configuration dictionary from :func:`load_config`.
    :type cfg: dict
    :param logger: logger instance for progress messages.
    :type logger: logging.Logger
    :return: ``None``
    :rtype: None
    """
    manifest_path = Path(cfg["output"]) / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest_safe(processed), indent=2))
    logger.info(f"wrote manifest -> {manifest_path}")
    return None


def get_args():
    """Parse the single ``--config``/``-c`` CLI argument.

    :return: parsed arguments namespace, exposing ``args.config``.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--config", "-c", required=True, help="Path to the JSON config file"
    )
    return parser.parse_args()


def main():
    """Entry point: load the config and run load -> process -> export.

    :return: ``None``
    :rtype: None
    """
    args = get_args()
    cfg = load_config(args.config)

    folder_output = Path(cfg["output"])
    folder_output.mkdir(parents=True, exist_ok=True)
    logger = get_logger(cfg["label"], folder_output / "logs.txt", talk=cfg["verbose"])

    logger.info("starting")
    t0 = time.time()

    loaded = load_data(cfg, logger)
    processed = process_data(loaded, cfg, logger)
    export_data(processed, cfg, logger)

    logger.info(f"run completed in {time.time() - t0:.2f} seconds")
    logger.info(f"results available at:\n\n\t{folder_output}\n")

    return None


if __name__ == "__main__":
    main()
