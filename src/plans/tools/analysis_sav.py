# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
analysis_sav -- stage-area-volume analysis, standalone PLANS tool.

For a range of water-surface stages (elevations), floods a DEM against
an AOI mask and computes the inundated area, mean depth and stored
volume at each stage. Exports a stage-area-volume (S-A-V) curve table,
optional per-stage depth rasters and preview images, an optional
animated GIF of the flooding sequence, and three curve plots
(stage x depth, stage x area, stage x volume).

Self-contained apart from the ``plans.datasets`` raster classes
(:class:`~plans.datasets.Elevation`, :class:`~plans.datasets.AOI`,
:class:`~plans.datasets.Depth`) -- no dependency on ``plans.tools.core``.
All parameters are passed through a single JSON config file.

Usage
-----

.. code-block:: bash

    python analysis_sav.py --config config.json

Config file
-----------

The ``--config``/``-c`` flag points to a JSON file. Template, ready to
copy and paste:

.. code-block:: json

    {
      "output": "C:/data/upacarai/depths",
      "label": "upacarai_dam",
      "dem": "C:/data/upacarai/topo/dem_bat2.tif",
      "aoi": "C:/data/upacarai/topo/dem_bat_aoi.tif",
      "stage_min": 146.0,
      "stage_max": 152.0,
      "cell_area_m2": 25.0,

      "project": "upacarai",
      "verbose": true,
      "structure_name": "Barragem Coradini",
      "stage_step": 0.1,
      "views": true,
      "export_rasters": true,
      "make_gif": true,
      "gif_duration": 0.3,
      "gif_loop": 0,
      "elevation_view_range": [145, 160],
      "elevation_view_bins": 50,
      "depth_view_range": [0, 5],
      "font_family": "Arial",
      "line_color": "#000080",
      "fig_width_cm": 12,
      "fig_height_cm": 6,
      "fig_dpi": 300
    }

Required fields
~~~~~~~~~~~~~~~~
* ``output`` (str) -- output folder for the table, rasters, previews,
  GIF and curve plots.
* ``label`` (str) -- run label, used as the filename prefix for every
  exported file.
* ``dem`` (str) -- path to the elevation/bathymetry raster.
* ``aoi`` (str) -- path to the AOI/basin mask raster.
* ``stage_min`` / ``stage_max`` (float) -- stage (water level) range
  to simulate, in the DEM's vertical units.
* ``cell_area_m2`` (float) -- DEM pixel area, in m². Must match the
  actual resolution of ``dem``, or the area/volume figures will be
  wrong.

Optional fields (defaults reproduce the original script's behaviour)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* ``project`` (str, default ``null``)
* ``verbose`` (bool, default ``false``) -- echo logs to console.
* ``structure_name`` (str, default ``""``) -- shown in per-stage titles.
* ``stage_step`` (float, default ``0.1``)
* ``views`` (bool, default ``true``) -- export a preview image per stage.
* ``export_rasters`` (bool, default ``true``) -- export a depth ``.tif`` per stage.
* ``make_gif`` (bool, default ``true``) -- assemble a GIF from the stage
  previews; requires ``"views": true``, since the GIF frames come from
  those previews.
* ``gif_duration`` (float, default ``0.3``) -- seconds per GIF frame.
* ``gif_loop`` (int, default ``0``) -- GIF loop count, ``0`` = infinite.
* ``elevation_view_range`` ([float, float] or ``null``, default ``null``)
  -- elevation histogram range for the preview plot; ``null`` lets it
  auto-scale.
* ``elevation_view_bins`` (int, default ``50``)
* ``depth_view_range`` ([float, float], default ``[0, 5]``) -- depth
  colour-scale range for the preview plot.
* ``font_family`` (str, default ``"Arial"``), ``line_color`` (str,
  default ``"#000080"``), ``fig_width_cm``/``fig_height_cm`` (float,
  default ``12``/``6``), ``fig_dpi`` (int, default ``300``) -- curve
  plot styling.

The ``REQUIRED``/``OPTIONAL`` dictionaries just below are the actual
validation source of truth -- keep them in sync with this docstring
whenever a field changes.
"""

# IMPORTS
# ***********************************************************************
import argparse
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import imageio

from plans.datasets import Elevation, AOI, Depth


# CONFIG SCHEMA
# ***********************************************************************
NUMBER = (int, float)

# Required fields: {name: type}
REQUIRED = {
    "output": str,
    "label": str,
    "dem": str,
    "aoi": str,
    "stage_min": NUMBER,
    "stage_max": NUMBER,
    "cell_area_m2": NUMBER,
}
# Optional fields: {name: (type, default)}
OPTIONAL = {
    "project": (str, None),
    "verbose": (bool, False),
    "structure_name": (str, ""),
    "stage_step": (NUMBER, 0.1),
    "views": (bool, True),
    "export_rasters": (bool, True),
    "make_gif": (bool, True),
    "gif_duration": (NUMBER, 0.3),
    "gif_loop": (int, 0),
    "elevation_view_range": (list, None),
    "elevation_view_bins": (int, 50),
    "depth_view_range": (list, [0, 5]),
    "font_family": (str, "Arial"),
    "line_color": (str, "#000080"),
    "fig_width_cm": (NUMBER, 12),
    "fig_height_cm": (NUMBER, 6),
    "fig_dpi": (int, 300),
}


def _type_name(t):
    """Return a human-readable name for a type or tuple of types.

    :param t: a type, or a tuple of acceptable types.
    :type t: type or tuple
    :return: ``" or "``-joined type name(s).
    :rtype: str
    """
    if isinstance(t, tuple):
        return " or ".join(x.__name__ for x in t)
    return t.__name__


def load_config(file_config):
    """Load, validate and fill defaults for the JSON config file.

    Checks that every key in :data:`REQUIRED` is present and of the
    right type, fills in defaults for missing :data:`OPTIONAL` keys,
    type-checks the ones that were provided, and enforces a couple of
    cross-field rules (range pairs, ``make_gif`` needing ``views``).

    :param file_config: path to the JSON config file.
    :type file_config: str or pathlib.Path
    :return: validated configuration dictionary, defaults included.
    :rtype: dict
    :raises ValueError: if a required field is missing, a field has
        the wrong type, or a cross-field rule is violated.
    """
    cfg = json.loads(Path(file_config).read_text())

    missing = [k for k in REQUIRED if k not in cfg]
    if missing:
        raise ValueError(f"Missing required config field(s): {missing}")

    for k, t in REQUIRED.items():
        if not isinstance(cfg[k], t):
            raise ValueError(
                f"Config field '{k}' must be {_type_name(t)}, got {type(cfg[k]).__name__}"
            )

    for k, (t, default) in OPTIONAL.items():
        cfg.setdefault(k, default)
        if cfg[k] is not None and not isinstance(cfg[k], t):
            raise ValueError(
                f"Config field '{k}' must be {_type_name(t)}, got {type(cfg[k]).__name__}"
            )

    for k in ("elevation_view_range", "depth_view_range"):
        if cfg[k] is not None and len(cfg[k]) != 2:
            raise ValueError(f"Config field '{k}' must be a [min, max] pair")

    if cfg["make_gif"] and not cfg["views"]:
        raise ValueError(
            "'make_gif' requires 'views' to be true (GIF frames come from the stage previews)"
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


# TOOL STEPS
# ***********************************************************************
def load_data(cfg, logger):
    """Load the DEM and AOI rasters and prepare the elevation grid.

    :param cfg: validated configuration dictionary.
    :type cfg: dict
    :param logger: logger instance for progress messages.
    :type logger: logging.Logger
    :return: ``(elevation, depth)`` raster objects, with the AOI mask
        already applied to ``elevation`` and view specs configured.
    :rtype: tuple
    """
    logger.info("loading DEM and AOI")

    aoi = AOI()
    aoi.load_data(Path(cfg["aoi"]))

    elevation = Elevation()
    elevation.load_data(Path(cfg["dem"]))
    elevation.apply_aoi_mask(grid_aoi=aoi.data)

    if cfg["elevation_view_range"] is not None:
        elevation.view_specs["range"] = tuple(cfg["elevation_view_range"])
    elevation.view_specs["bins"] = cfg["elevation_view_bins"]

    depth = Depth()
    depth.copy_structure(raster_ref=elevation)

    return elevation, depth


def process_data(loaded, cfg, logger):
    """Run the stage-area-volume simulation across the configured stage range.

    For each stage, floods every DEM cell below the stage elevation,
    computes inundated area, mean depth and stored volume, and
    optionally exports a depth raster and/or a preview image for that
    stage (the previews double as GIF frames, in stage order).

    :param loaded: ``(elevation, depth)`` tuple returned by :func:`load_data`.
    :type loaded: tuple
    :param cfg: validated configuration dictionary.
    :type cfg: dict
    :param logger: logger instance for progress messages.
    :type logger: logging.Logger
    :return: dict with the S-A-V curve table (``"df"``) and the list of
        per-stage preview image paths in stage order (``"image_paths"``).
    :rtype: dict
    """
    elevation, depth = loaded
    folder_output = Path(cfg["output"])
    prefix = cfg["label"]

    ls_stage = np.arange(cfg["stage_min"], cfg["stage_max"], cfg["stage_step"])

    ls_areas = []
    ls_volumes = []
    ls_depth_mean = []
    ls_image_paths = []

    for v in ls_stage:
        nm = "{}_depth_{}".format(prefix, str(round(v, 2)).zfill(3)).replace(".", "P")
        grid_mask = np.where(elevation.data < v, 1, 0)

        if np.sum(grid_mask) == 0:
            ls_areas.append(0)
            ls_volumes.append(0)
            ls_depth_mean.append(0)
            logger.info(f"stage {v:.2f}m -- no inundated cells")
            continue

        grid_depth = v - elevation.data
        depth.set_data(grid=grid_depth)
        depth.apply_aoi_mask(grid_aoi=grid_mask)

        area = np.nansum(grid_mask) * cfg["cell_area_m2"]
        depth_mean = np.nanmean(depth.data)
        volume = area * depth_mean

        title_prefix = f"{cfg['structure_name']} " if cfg["structure_name"] else ""
        s = (
            f"{title_prefix}Z={v:.1f}m  D={depth_mean:.2f}m  "
            f"A={area / (100 * 100):.1f}ha  V={volume / 1000:.1f}×10³m³"
        )
        logger.info(s)

        if cfg["views"]:
            depth.view_specs["range"] = tuple(cfg["depth_view_range"])
            depth.view_specs["folder"] = folder_output
            depth.view_specs["filename"] = nm
            depth.view_specs["title"] = s
            depth.view(show=False)

            img_path = folder_output / f"{nm}.jpg"
            if not img_path.exists():
                img_path = folder_output / f"{nm}.png"
            if img_path.exists():
                ls_image_paths.append(img_path)
            else:
                logger.info(
                    f"no preview image found for stage {v:.2f}m, skipping in GIF"
                )

        if cfg["export_rasters"]:
            depth.export(folder=folder_output, filename=nm)

        ls_areas.append(area)
        ls_volumes.append(volume)
        ls_depth_mean.append(depth_mean)

        depth.release_aoi_mask()

    df = pd.DataFrame(
        {
            "Cota_m": ls_stage,
            "Profundidade_Media_m": ls_depth_mean,
            "Area_m2": ls_areas,
            "Volume_m3": ls_volumes,
        }
    )

    return {"df": df, "image_paths": ls_image_paths}


def export_data(processed, cfg, logger):
    """Export the S-A-V curve table, optional GIF, and curve plots.

    :param processed: dict returned by :func:`process_data`, with keys
        ``"df"`` and ``"image_paths"``.
    :type processed: dict
    :param cfg: validated configuration dictionary.
    :type cfg: dict
    :param logger: logger instance for progress messages.
    :type logger: logging.Logger
    :return: ``None``
    :rtype: None
    """
    df = processed["df"]
    image_paths = processed["image_paths"]
    folder_output = Path(cfg["output"])
    prefix = cfg["label"]

    file_csv = folder_output / f"{prefix}_stage_area_volume.csv"
    df.to_csv(file_csv, sep=",", index=False)
    logger.info(f"exporting table >>> {file_csv.name}")

    if cfg["make_gif"]:
        if image_paths:
            gif_path = folder_output / f"{prefix}_stage_simulation.gif"
            frames = [imageio.imread(p) for p in image_paths]
            imageio.mimsave(
                gif_path, frames, duration=cfg["gif_duration"], loop=cfg["gif_loop"]
            )
            logger.info(f"exporting gif >>> {gif_path.name}")
        else:
            logger.info("no preview images collected, GIF was not created")

    mpl.rcParams["font.family"] = cfg["font_family"]
    cm_to_in = 1 / 2.54
    fig_width = cfg["fig_width_cm"] * cm_to_in
    fig_height = cfg["fig_height_cm"] * cm_to_in

    def plot_curve(x, y, xlabel, ylabel, filename):
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=cfg["fig_dpi"])
        ax.plot(x, y, color=cfg["line_color"], linewidth=1.8)
        ax.set_xlabel(xlabel, fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.tick_params(axis="both", labelsize=8)
        ax.grid(True, linewidth=0.4, alpha=0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        fig.savefig(folder_output / filename, dpi=cfg["fig_dpi"])
        plt.close(fig)
        logger.info(f"exporting fig >>> {filename}")

    plot_curve(
        x=df["Cota_m"],
        y=df["Profundidade_Media_m"],
        xlabel="Z (m)",
        ylabel="D (m)",
        filename=f"{prefix}_curve_stage_depth.jpg",
    )
    plot_curve(
        x=df["Cota_m"],
        y=df["Area_m2"] / (100 * 100),
        xlabel="Z (m)",
        ylabel="A (ha)",
        filename=f"{prefix}_curve_stage_area.jpg",
    )
    plot_curve(
        x=df["Cota_m"],
        y=df["Volume_m3"] / 1000,
        xlabel="Z (m)",
        ylabel="V (\u00d710\u00b3m\u00b3)",
        filename=f"{prefix}_curve_stage_volume.jpg",
    )

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
