# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
<tool_name> -- standalone PLANS tool.

Self-contained script: copy this single file anywhere and run it with
Python 3. It has no dependency on the ``plans.tools.core`` module --
all parameters are passed through a single JSON config file.

Usage
-----

.. code-block:: bash

    python <tool_name>.py --config config.json

Config file
-----------

The ``--config``/``-c`` flag points to a JSON file. Template, ready to
copy and paste:

.. code-block:: json

    {
      "output": "C:/data/run1",
      "label": "catchment_v1",
      "climate": "era5.csv",

      "project": "my_project",
      "verbose": true,
      "views": true,
      "lulc": "lulc_2020.tif"
    }

Required fields
~~~~~~~~~~~~~~~~
* ``output`` (str) -- output folder for run artifacts.
* ``label`` (str) -- run label, used as the logger name.
* ``climate`` (str) -- path to the climate series file.

Optional fields
~~~~~~~~~~~~~~~~
* ``project`` (str, default ``null``) -- project name.
* ``verbose`` (bool, default ``false``) -- echo logs to console.
* ``views`` (bool, default ``false``) -- also export figures.
* ``lulc`` (str, default ``null``) -- path to the LULC raster file.

The ``REQUIRED``/``OPTIONAL`` dictionaries just below are the actual
validation source of truth -- keep them in sync with this docstring
whenever you add, rename or remove a field.
"""

# IMPORTS
# ***********************************************************************
import argparse
import json
import logging
import time
from pathlib import Path


# CONFIG SCHEMA
# ***********************************************************************
# Required fields: {name: type}
REQUIRED = {
    "output": str,
    "label": str,
    "climate": str,
}
# Optional fields: {name: (type, default)}
OPTIONAL = {
    "project": (str, None),
    "verbose": (bool, False),
    "views": (bool, False),
    "lulc": (str, None),
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


# TOOL STEPS -- fill in the actual logic for this tool here
# ***********************************************************************
def load_data(cfg, logger):
    """Load input data described by ``cfg``.

    :param cfg: validated configuration dictionary from :func:`load_config`.
    :type cfg: dict
    :param logger: logger instance for progress messages.
    :type logger: logging.Logger
    :return: loaded data, in whatever form suits this tool.
    :rtype: object
    """
    logger.info("loading inputs")
    # ... {develop}
    return None


def process_data(loaded, cfg, logger):
    """Process data returned by :func:`load_data`.

    :param loaded: data returned by :func:`load_data`.
    :type loaded: object
    :param cfg: validated configuration dictionary from :func:`load_config`.
    :type cfg: dict
    :param logger: logger instance for progress messages.
    :type logger: logging.Logger
    :return: processed data, in whatever form suits this tool.
    :rtype: object
    """
    logger.info("processing data")
    # ... {develop}
    return None


def export_data(processed, cfg, logger):
    """Export results returned by :func:`process_data`.

    :param processed: data returned by :func:`process_data`.
    :type processed: object
    :param cfg: validated configuration dictionary from :func:`load_config`.
    :type cfg: dict
    :param logger: logger instance for progress messages.
    :type logger: logging.Logger
    :return: ``None``
    :rtype: None
    """
    logger.info("exporting outputs")
    # ... {develop}
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
