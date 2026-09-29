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
3. Anomalies -- monthly and annual, absolute, relative/percent, and
   z-score (standardized, i.e. anomaly divided by the standard-deviation
   normal).

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
      "low_memory": false,
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
        "relative": true,
        "zscore": true
      },
      "styles": {
        "annual": "styles/annual.qml",
        "annual_normal": "styles/annual_normal.qml",
        "monthly_normal": "styles/monthly_normal.qml",
        "anomaly_absolute": "styles/anomaly_absolute.qml",
        "anomaly_relative": "styles/anomaly_relative.qml",
        "anomaly_zscore": "styles/anomaly_zscore.qml"
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
* ``low_memory`` (bool, default ``false``) -- when ``true``, process
  rasters one at a time using incremental (online) accumulators instead
  of stacking the entire series in RAM. Trades speed for memory: the
  footprint drops from O(N × pixels) to O(pixels) for mean, sum, min,
  max, and std. Percentile/median stats use a temporary memory-mapped
  file on disk and are computed in spatial chunks, so they are slower but
  still bounded. Enable this when the uncompressed time series does not
  fit in available RAM.
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
  (bool, default ``true``), ``zscore`` (bool, default ``false``). When
  ``zscore`` is ``true``, ``"std"`` is required among ``normals.stats``
  (it is added automatically with a log message if missing, same as
  ``"mean"`` is for anomalies generally).
* ``styles`` (dict, default ``{}``) -- see :func:`apply_style`. Each key
  is optional; when present, its value is a path to a QGIS ``.qml`` style
  template that gets copied as a same-named sidecar next to every raster
  in that output category, so QGIS auto-applies it on load. Keys:
  ``annual`` (the per-year aggregates), ``annual_normal``,
  ``monthly_normal``, ``anomaly_absolute`` (used for both monthly and
  annual absolute anomalies), ``anomaly_relative`` (ditto, relative
  anomalies), and ``anomaly_zscore`` (ditto, z-score anomalies).

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
import os
import re
import shutil
import tempfile
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
    "low_memory": (bool, False),
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

# Fixed filename convention: "..._<YYYY>-<MM>.<ext>"
_DATE_SUFFIX_RE = re.compile(r"_(\d{4})-(\d{2})(?=\.[A-Za-z0-9]+$)")

_BASE_STAT_FUNCS: dict[str, Callable] = {
    "mean": np.nanmean,
    "sum": np.nansum,
    "max": np.nanmax,
    "min": np.nanmin,
    "median": np.nanmedian,
    "std": np.nanstd,
}
_PCT_RE = re.compile(r"^p(\d{1,3})$")

INT16_NODATA = np.iinfo(np.int16).max  # 32767


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


def _is_percentile_stat(stat: str) -> bool:
    """Return True if ``stat`` requires the full temporal stack (median or pN).

    :param stat: Statistic name.
    :type stat: str
    :returns: True for ``"median"`` and ``"pN"`` stats.
    :rtype: bool
    """
    return stat == "median" or bool(_PCT_RE.match(stat))


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


def _write_raster_int16(arr, profile, out_path, scale=100, nodata=INT16_NODATA):
    """Write a single-band Int16 raster, scaling and rounding first.

    Values are multiplied by ``scale``, rounded to the nearest integer, and
    cast to Int16. NaNs map to ``nodata``. Values whose scaled magnitude
    exceeds the Int16 range (~ ±32767) wrap around silently on cast --
    a deliberate size/precision tradeoff, not a clipped/saturated cast.

    :param arr: pixel array to write (e.g. percent relative anomaly).
    :type arr: numpy.ndarray
    :param profile: rasterio profile to reuse; dtype/count/nodata are overridden.
    :type profile: dict
    :param out_path: output file path.
    :type out_path: str or pathlib.Path
    :param scale: multiplier applied before rounding, e.g. 100 to preserve
        two decimal places of a percent value as an integer.
    :type scale: int or float
    :param nodata: sentinel value for NaN pixels.
    :type nodata: int
    :returns: None
    :rtype: None
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        scaled = np.round(arr * scale)
        out = np.where(np.isfinite(scaled), scaled, nodata).astype(np.int16)

    out_profile = profile.copy()
    out_profile.update(dtype="int16", count=1, nodata=nodata)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out_path, "w", **out_profile) as dst:
        dst.write(out, 1)


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


# ONLINE (LOW-MEMORY) REDUCTION
# ***********************************************************************
#
# Replaces the ``_read_stack`` + ``_apply_stat`` pattern with one-at-a-time
# incremental accumulators. Memory footprint drops from O(N × pixels) to
# O(pixels) for mean, sum, min, max, and std. Percentile/median stats fall
# back to a disk-backed ``np.memmap`` processed in spatial chunks.

_ONLINE_CHUNK_ROWS = 512  # rows per chunk when computing percentiles


class _OnlineReducer:
    """Incremental pixel-wise reducer -- feeds one raster at a time.

    Maintains only the accumulators needed by the requested ``stats``:

    * ``mean``, ``sum``, ``std`` -- running sum, sum-of-squares, and
      per-pixel valid-count. ``std`` uses the textbook
      ``sqrt(E[x²] - E[x]²)`` formula (ddof=0, matching ``np.nanstd``);
      numerically safe for typical geophysical value ranges.
    * ``min``, ``max`` -- running extrema via ``np.fmin`` / ``np.fmax``
      (NaN-skipping).
    * ``median``, ``pN`` -- require the full stack, so they are stored in
      a temporary ``np.memmap`` file and computed in spatial chunks at
      :meth:`result` time.

    :param stats: statistic names requested.
    :type stats: list[str]
    :param n_layers: total number of rasters that will be fed (needed to
        pre-allocate the memmap for percentile stats).
    :type n_layers: int
    :param tmpdir: directory for the memmap temp file; defaults to the
        system temp directory.
    :type tmpdir: str or pathlib.Path or None
    """

    def __init__(self, stats: list[str], n_layers: int, tmpdir=None):
        self._stats = list(stats)
        self._n_layers = n_layers
        self._fed = 0
        self._shape = None  # set on first feed
        self._tmpdir = tmpdir

        # Classify which accumulators we need
        self._need_sum = False
        self._need_sum_sq = False
        self._need_min = False
        self._need_max = False
        self._pct_stats: list[str] = []

        for s in stats:
            if s in ("mean", "sum"):
                self._need_sum = True
            elif s == "std":
                self._need_sum = True
                self._need_sum_sq = True
            elif s == "min":
                self._need_min = True
            elif s == "max":
                self._need_max = True
            elif _is_percentile_stat(s):
                self._pct_stats.append(s)
            else:
                # Will raise later via _resolve_stat_func if truly unknown
                raise ValueError(f"Unknown stat '{s}' for online reducer")

        # Lazy-initialized arrays
        self._count: Optional[np.ndarray] = None
        self._sum: Optional[np.ndarray] = None
        self._sum_sq: Optional[np.ndarray] = None
        self._min_arr: Optional[np.ndarray] = None
        self._max_arr: Optional[np.ndarray] = None

        # Memmap for percentile stats
        self._mm_path: Optional[str] = None
        self._mm: Optional[np.ndarray] = None

    def _init_arrays(self, shape):
        """Allocate accumulators once the raster shape is known."""
        self._shape = shape
        self._count = np.zeros(shape, dtype="int32")
        if self._need_sum:
            self._sum = np.zeros(shape, dtype="float64")
        if self._need_sum_sq:
            self._sum_sq = np.zeros(shape, dtype="float64")
        if self._need_min:
            self._min_arr = np.full(shape, np.nan, dtype="float64")
        if self._need_max:
            self._max_arr = np.full(shape, np.nan, dtype="float64")
        if self._pct_stats:
            fd, path = tempfile.mkstemp(
                suffix=".mmap", dir=self._tmpdir, prefix="plans_pct_"
            )
            os.close(fd)
            self._mm_path = path
            self._mm = np.memmap(
                path,
                dtype="float32",
                mode="w+",
                shape=(self._n_layers, *shape),
            )

    def feed(self, arr: np.ndarray) -> None:
        """Incorporate one raster layer into the running accumulators.

        :param arr: 2-D pixel array (float64, NaN = nodata).
        :type arr: numpy.ndarray
        """
        if self._shape is None:
            self._init_arrays(arr.shape)

        valid = np.isfinite(arr)
        self._count += valid

        if self._sum is not None:
            self._sum += np.where(valid, arr, 0.0)
        if self._sum_sq is not None:
            self._sum_sq += np.where(valid, arr * arr, 0.0)
        if self._min_arr is not None:
            self._min_arr = np.fmin(self._min_arr, arr)
        if self._max_arr is not None:
            self._max_arr = np.fmax(self._max_arr, arr)
        if self._mm is not None:
            self._mm[self._fed] = arr.astype("float32")

        self._fed += 1

    def result(self, stat: str) -> np.ndarray:
        """Compute the final result for one requested statistic.

        :param stat: statistic name (must be one passed to ``__init__``).
        :type stat: str
        :returns: 2-D result array (float64, NaN where no valid data).
        :rtype: numpy.ndarray
        """
        no_data = self._count == 0

        if stat == "mean":
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                out = self._sum / self._count
            out[no_data] = np.nan
            return out

        if stat == "sum":
            out = self._sum.copy()
            out[no_data] = np.nan
            return out

        if stat == "std":
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                mean = self._sum / self._count
                var = self._sum_sq / self._count - mean * mean
                out = np.sqrt(np.maximum(var, 0.0))
            out[no_data] = np.nan
            return out

        if stat == "min":
            return self._min_arr.copy()

        if stat == "max":
            return self._max_arr.copy()

        if stat == "median":
            return self._percentile_chunked(50)

        m = _PCT_RE.match(stat)
        if m:
            return self._percentile_chunked(int(m.group(1)))

        raise ValueError(f"Unknown stat '{stat}'")

    def _percentile_chunked(self, q: int) -> np.ndarray:
        """Compute nanpercentile from the memmap in spatial row-chunks.

        :param q: percentile (0-100).
        :type q: int
        :returns: 2-D result array.
        :rtype: numpy.ndarray
        """
        H, W = self._shape
        result = np.full((H, W), np.nan, dtype="float64")
        for r0 in range(0, H, _ONLINE_CHUNK_ROWS):
            r1 = min(r0 + _ONLINE_CHUNK_ROWS, H)
            # Load only this row-chunk from the memmap into RAM
            chunk = np.array(
                self._mm[: self._fed, r0:r1, :], dtype="float64"
            )
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                result[r0:r1, :] = np.nanpercentile(chunk, q, axis=0)
        return result

    def cleanup(self) -> None:
        """Delete the temporary memmap file, if any."""
        if self._mm is not None:
            del self._mm
            self._mm = None
        if self._mm_path and os.path.exists(self._mm_path):
            os.unlink(self._mm_path)
            self._mm_path = None


def _reduce_rasters(
    records: list[MonthlyRaster],
    stats: list[str],
    low_memory: bool = False,
    tmpdir=None,
) -> tuple[dict[str, np.ndarray], dict]:
    """Reduce a list of rasters to per-stat result arrays.

    Central dispatch: when ``low_memory`` is False, uses the original
    stack-in-RAM approach (``_read_stack`` + ``_apply_stat``); when True,
    uses the incremental ``_OnlineReducer``.

    :param records: rasters to reduce, in order.
    :type records: list[MonthlyRaster]
    :param stats: statistic names to compute.
    :type stats: list[str]
    :param low_memory: use incremental one-at-a-time reduction.
    :type low_memory: bool
    :param tmpdir: temp directory for memmap files (low_memory + percentile
        stats only).
    :type tmpdir: str or pathlib.Path or None
    :returns: ``({stat: result_array}, rasterio_profile)``.
    :rtype: tuple[dict[str, numpy.ndarray], dict]
    """
    if not low_memory:
        stack, profile = _read_stack(records)
        results = {}
        for stat in stats:
            func = _resolve_stat_func(stat)
            results[stat] = _apply_stat(stack, func)
        return results, profile

    # -- low-memory path --
    reducer = _OnlineReducer(stats, n_layers=len(records), tmpdir=tmpdir)
    profile = None
    for r in records:
        arr, prof = _read_as_float(r.path)
        if profile is None:
            profile = prof
        reducer.feed(arr)
    results = {stat: reducer.result(stat) for stat in stats}
    reducer.cleanup()
    return results, profile


# PIPELINE STEPS -- annual aggregation, normals, anomalies
# ***********************************************************************


def aggregate_annual(
    monthly_rasters: list[MonthlyRaster],
    output_dir,
    logger,
    stats: list[str] = ("mean",),
    min_months: int = 12,
    file_prefix: str = "annual",
    low_memory: bool = False,
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
    :param low_memory: Use incremental reduction instead of stacking.
    :type low_memory: bool
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
        results, profile = _reduce_rasters(
            recs_sorted, stats, low_memory=low_memory, tmpdir=str(output_dir)
        )

        for stat in stats:
            out_path = output_dir / f"{file_prefix}_{stat}_{year}.tif"
            _write_raster(results[stat], profile, out_path)
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
    low_memory: bool = False,
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
    :param low_memory: Use incremental reduction instead of stacking.
    :type low_memory: bool
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
    results, profile = _reduce_rasters(
        recs, stats, low_memory=low_memory, tmpdir=str(output_dir)
    )

    output_paths = {}
    for stat in stats:
        out_path = output_dir / f"{file_prefix}_{stat}.tif"
        _write_raster(results[stat], profile, out_path)
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
    low_memory: bool = False,
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
    :param low_memory: Use incremental reduction instead of stacking.
    :type low_memory: bool
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

        results, profile = _reduce_rasters(
            month_recs, stats, low_memory=low_memory, tmpdir=str(output_dir)
        )

        for stat in stats:
            out_path = output_dir / f"{file_prefix}_{month:02d}_{stat}.tif"
            _write_raster(results[stat], profile, out_path)
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
    zscore: bool = False,
    normal_stat: str = "mean",
    std_stat: str = "std",
) -> dict[str, dict[tuple[int, int], str]]:
    """Compute per-month anomalies against the calendar-month normal.

    For every monthly raster, computes::

        anomaly          = value - normal[month]
        relative_anomaly = (value - normal[month]) / normal[month] * 100   # percent
        zscore           = (value - normal[month]) / std[month]           # dimensionless

    where ``normal`` is the ``normal_stat`` monthly normal (``"mean"`` by
    default -- anomalies are conventionally defined relative to the mean)
    and ``std`` is the ``std_stat`` monthly normal (the per-calendar-month
    standard deviation across the normals horizon). Pixels where ``normal``
    is exactly 0 get ``NaN`` for the relative anomaly (percent deviation is
    undefined there) but still get a valid absolute anomaly -- relevant for
    variables like precipitation with dry-season zeros. Likewise, pixels
    where ``std`` is exactly 0 (e.g. a constant time series at that pixel)
    get ``NaN`` for the z-score.

    :param monthly_rasters: Parsed monthly rasters, as returned by
        :func:`parse_monthly_rasters`.
    :type monthly_rasters: list[MonthlyRaster]
    :param monthly_normal_paths_by_stat: Monthly normals, as returned by
        :func:`compute_monthly_normals`.
    :type monthly_normal_paths_by_stat: dict[str, dict[int, str]]
    :param output_dir: Base directory; ``absolute/``, ``relative/``, and
        ``zscore/`` subdirectories are created under it as needed.
    :type output_dir: str or pathlib.Path
    :param logger: Logger instance for progress messages.
    :type logger: logging.Logger
    :param relative: Whether to also compute the percent anomaly.
    :type relative: bool
    :param zscore: Whether to also compute the z-score (standardized)
        anomaly, i.e. the anomaly divided by the ``std_stat`` monthly
        normal.
    :type zscore: bool
    :param normal_stat: Which monthly normal stat to use as the baseline.
    :type normal_stat: str
    :param std_stat: Which monthly normal stat to use as the standard
        deviation for the z-score. Only read when ``zscore`` is ``true``.
    :type std_stat: str
    :returns: ``{"absolute": {(year, month): path}, "relative": {(year, month): path},
        "zscore": {(year, month): path}}``. ``"relative"``/``"zscore"`` are
        empty dicts when the corresponding flag is ``false``.
    :rtype: dict[str, dict[tuple[int, int], str]]
    :raises ValueError: If ``normal_stat`` was not computed in
        ``monthly_normal_paths_by_stat``, or ``zscore`` is ``true`` and
        ``std_stat`` was not computed there.
    """
    output_dir = Path(output_dir)
    if normal_stat not in monthly_normal_paths_by_stat:
        msg = (
            f"normal_stat '{normal_stat}' not found among computed monthly normal stats "
            f"(available: {list(monthly_normal_paths_by_stat)})"
        )
        logger.error(msg)
        raise ValueError(msg)
    if zscore and std_stat not in monthly_normal_paths_by_stat:
        msg = (
            f"std_stat '{std_stat}' not found among computed monthly normal stats "
            f"(available: {list(monthly_normal_paths_by_stat)}); zscore anomalies "
            f"require '{std_stat}' in normals.stats"
        )
        logger.error(msg)
        raise ValueError(msg)

    normal_by_month = monthly_normal_paths_by_stat[normal_stat]
    std_by_month = monthly_normal_paths_by_stat.get(std_stat, {}) if zscore else {}

    # Group input rasters by calendar month so we load only one month's
    # normals at a time (2 arrays: mean + std) instead of all 24.
    by_month: dict[int, list[MonthlyRaster]] = {}
    for r in monthly_rasters:
        by_month.setdefault(r.month, []).append(r)

    abs_dir = output_dir / "absolute"
    rel_dir = output_dir / "relative"
    z_dir = output_dir / "zscore"

    abs_paths: dict[tuple[int, int], str] = {}
    rel_paths: dict[tuple[int, int], str] = {}
    z_paths: dict[tuple[int, int], str] = {}

    for month in range(1, 13):
        month_recs = by_month.get(month, [])
        if not month_recs:
            continue

        # Load only this calendar month's normals
        if month not in normal_by_month:
            logger.warning(
                f"no '{normal_stat}' normal for month {month:02d}, "
                f"skipping anomalies for all {month:02d} rasters"
            )
            continue
        normal_arr, _ = _read_as_float(normal_by_month[month])

        std_arr = None
        if zscore:
            if month in std_by_month:
                std_arr, _ = _read_as_float(std_by_month[month])
            else:
                logger.warning(
                    f"no '{std_stat}' normal for month {month:02d}, "
                    f"skipping zscore anomalies for all {month:02d} rasters"
                )

        for r in month_recs:
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
                _write_raster_int16(rel_anomaly, profile, out_path_rel, scale=100)
                rel_paths[(r.year, r.month)] = str(out_path_rel)

            if zscore and std_arr is not None:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                    z_anomaly = anomaly / std_arr
                    z_anomaly = np.where(std_arr == 0, np.nan, z_anomaly)
                out_path_z = z_dir / f"anomaly_z_{r.year}_{r.month:02d}.tif"
                _write_raster_int16(z_anomaly, profile, out_path_z, scale=100)
                z_paths[(r.year, r.month)] = str(out_path_z)

            del arr, anomaly  # release before next raster

        logger.info(
            f"month {month:02d} anomalies: {len(month_recs)} raster(s) "
            f"(relative={'yes' if relative else 'no'}, zscore={'yes' if zscore else 'no'})"
        )
        del normal_arr, std_arr  # release before next month

    logger.info(
        f"anomalies computed for {len(abs_paths)} monthly raster(s) "
        f"(relative={'yes' if relative else 'no'}, zscore={'yes' if zscore else 'no'}), "
        f"baseline stat='{normal_stat}'"
        + (f", std stat='{std_stat}'" if zscore else "")
    )

    return {"absolute": abs_paths, "relative": rel_paths, "zscore": z_paths}


def compute_annual_anomalies(
    annual_paths_by_stat: dict[str, dict[int, str]],
    annual_normal_paths_by_stat: dict[str, str],
    output_dir,
    logger,
    base_stat: str = "mean",
    relative: bool = True,
    zscore: bool = False,
    std_stat: str = "std",
) -> dict[str, dict[int, str]]:
    """Compute per-year anomalies against the mean annual normal.

    For every year in the annual series identified by ``base_stat`` (e.g. the
    per-year ``"sum"`` rasters from :func:`aggregate_annual`, for a total like
    annual precipitation), computes::

        anomaly          = annual_value[year] - annual_normal_mean
        relative_anomaly = (annual_value[year] - annual_normal_mean) / annual_normal_mean * 100   # percent
        zscore           = (annual_value[year] - annual_normal_mean) / annual_normal_std          # dimensionless

    The baseline is always the ``"mean"`` entry of ``annual_normal_paths_by_stat``,
    matching the convention used for the monthly anomalies. The z-score
    divides by the ``std_stat`` entry (``"std"`` by default) of the same
    dict -- the interannual standard deviation over the normals horizon.
    Pixels where that std is exactly 0 get ``NaN`` for the z-score.

    :param annual_paths_by_stat: Per-year annual rasters, as returned by
        :func:`aggregate_annual`.
    :type annual_paths_by_stat: dict[str, dict[int, str]]
    :param annual_normal_paths_by_stat: Annual normals, as returned by
        :func:`compute_annual_normals`; must include a ``"mean"`` entry
        (and a ``std_stat`` entry when ``zscore`` is ``true``).
    :type annual_normal_paths_by_stat: dict[str, str]
    :param output_dir: Base directory; ``absolute/``, ``relative/``, and
        ``zscore/`` subdirectories are created under it as needed.
    :type output_dir: str or pathlib.Path
    :param logger: Logger instance for progress messages.
    :type logger: logging.Logger
    :param base_stat: Which annual series in ``annual_paths_by_stat`` to
        compute anomalies for.
    :type base_stat: str
    :param relative: Whether to also compute the percent anomaly.
    :type relative: bool
    :param zscore: Whether to also compute the z-score (standardized)
        anomaly, i.e. the anomaly divided by the ``std_stat`` annual
        normal.
    :type zscore: bool
    :param std_stat: Which annual normal stat to use as the standard
        deviation for the z-score. Only read when ``zscore`` is ``true``.
    :type std_stat: str
    :returns: ``{"absolute": {year: path}, "relative": {year: path},
        "zscore": {year: path}}``. ``"relative"``/``"zscore"`` are empty
        dicts when the corresponding flag is ``false``.
    :rtype: dict[str, dict[int, str]]
    :raises ValueError: If ``base_stat`` was not computed in
        ``annual_paths_by_stat``, the ``"mean"`` annual normal is missing,
        or ``zscore`` is ``true`` and ``std_stat`` was not computed.
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
    if zscore and std_stat not in annual_normal_paths_by_stat:
        msg = (
            f"annual normal '{std_stat}' was not computed (available: "
            f"{list(annual_normal_paths_by_stat)}); zscore anomalies require "
            f"'{std_stat}' in normals.stats"
        )
        logger.error(msg)
        raise ValueError(msg)

    normal_arr, _ = _read_as_float(annual_normal_paths_by_stat["mean"])
    std_arr = None
    if zscore:
        std_arr, _ = _read_as_float(annual_normal_paths_by_stat[std_stat])
    series = annual_paths_by_stat[base_stat]

    abs_dir = output_dir / "absolute"
    rel_dir = output_dir / "relative"
    z_dir = output_dir / "zscore"

    abs_paths: dict[int, str] = {}
    rel_paths: dict[int, str] = {}
    z_paths: dict[int, str] = {}

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
            _write_raster_int16(rel_anomaly, profile, out_path_rel, scale=100)
            rel_paths[year] = str(out_path_rel)

        if zscore:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                z_anomaly = anomaly / std_arr
                z_anomaly = np.where(std_arr == 0, np.nan, z_anomaly)
            out_path_z = z_dir / f"anomaly_z_{year}.tif"
            _write_raster_int16(z_anomaly, profile, out_path_z, scale=100)
            z_paths[year] = str(out_path_z)

    logger.info(
        f"annual anomalies computed for {len(abs_paths)} year(s) "
        f"(relative={'yes' if relative else 'no'}, zscore={'yes' if zscore else 'no'}), "
        f"baseline='mean' of '{base_stat}' series"
        + (f", std stat='{std_stat}'" if zscore else "")
    )

    return {"absolute": abs_paths, "relative": rel_paths, "zscore": z_paths}


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
    low_memory = cfg.get("low_memory", False)

    if low_memory:
        logger.info("low_memory mode enabled -- using incremental reduction")

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
    anomalies_zscore = anomalies_cfg.get("zscore", False)

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

    if (
        anomalies_zscore
        and (anomalies_monthly_enabled or anomalies_annual_enabled)
        and "std" not in normal_stats
    ):
        normal_stats.append("std")
        logger.info(
            "adding 'std' to normals.stats (required by anomalies.zscore)"
        )

    annual_paths = aggregate_annual(
        monthly,
        output_dir / "annual",
        logger,
        stats=annual_stats,
        min_months=min_months,
        low_memory=low_memory,
    )
    _maybe_apply_style(annual_paths, styles_cfg.get("annual"), logger)

    annual_normal_paths = compute_annual_normals(
        annual_paths,
        output_dir / "normals" / "annual",
        logger,
        base_stat=annual_base_stat,
        stats=normal_stats,
        horizon=annual_horizon,
        low_memory=low_memory,
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
            zscore=anomalies_zscore,
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
        if anomalies_zscore:
            _maybe_apply_style(
                annual_anomaly_paths["zscore"],
                styles_cfg.get("anomaly_zscore"),
                logger,
            )

    monthly_normal_paths = compute_monthly_normals(
        monthly,
        output_dir / "normals" / "monthly",
        logger,
        stats=normal_stats,
        horizon=monthly_horizon,
        low_memory=low_memory,
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
            zscore=anomalies_zscore,
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
        if anomalies_zscore:
            _maybe_apply_style(
                monthly_anomaly_paths["zscore"],
                styles_cfg.get("anomaly_zscore"),
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