# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Performance smoke tests for the ``databases`` module.

Features
--------
The test suite times, without strict time assertions:

* Inserting 1,000,000 hourly records into a ``DataBase`` and querying one year.
* Inserting 1,200,000 monthly records (100,000 cells) into a ``SemiSpatialDB``
  and querying 40,000 cells, above the SQLite cap on bound parameters.

Timings are printed; only row counts are asserted.

"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import unittest
import json, shutil, tempfile, time
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
import numpy as np
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from plans.databases import DataBase, SemiSpatialDB

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

SPEC = {
    "name": "BENCH",
    "abstract": "Synthetic benchmark series",
    "method": "random",
    "timestep": "1H",
    "extent": "point",
    "scale": 1,
    "offset": 0,
    "start": "2000-01-01",
    "end": None,
    "variable_name": "precipitation",
    "statistic_name": "sum",
    "source_name": "CHIRPS v2.0",
}

# ... {develop}

# FUNCTIONS
# ***********************************************************************


def timed(label, func):
    # run func, print elapsed time and return its result
    t0 = time.perf_counter()
    result = func()
    print(f"[bcmk databases] {label}: {time.perf_counter() - t0:.2f}s")
    return result


# CLASSES
# ***********************************************************************


class TestDataBasePerformance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests in this class: create the temp folder and specs file.
        """
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.file_specs = cls.temp_dir / "specs.json"
        cls.file_specs.write_text(json.dumps([SPEC]), encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        """
        Runs once after all tests in this class.
        """
        shutil.rmtree(cls.temp_dir)
        return None

    def _new(self, db_class, name):
        db = db_class(name=name)
        db.new(
            config={
                "database": {"path": str(self.temp_dir / f"{name}.db")},
                "specs": {"path": str(self.file_specs)},
            }
        )
        return db

    def test_base_hourly(self):
        db = self._new(db_class=DataBase, name="base")
        n = 1_000_000
        dates = pd.date_range("2000-01-01", periods=n, freq="h", tz="UTC")
        df = pd.DataFrame({"datetime": dates.astype(str), "value": np.random.rand(n)})
        timed(
            label=f"insert {n:,} rows",
            func=lambda: db.insert_records(dataframe=df, spec_name="BENCH", flag=1),
        )
        query = {"spec_name": "BENCH", "start": "2050-01-01", "end": "2050-12-31"}
        result = timed(
            label="query one year",
            func=lambda: db.query_records(query_dict=query),
        )
        db.close()
        # 2050 is not a leap year; end bound is inclusive at 00:00
        self.assertEqual(len(result), 364 * 24 + 1)

    def test_semispatial_monthly(self):
        db = self._new(db_class=SemiSpatialDB, name="semi")
        ncell = 100_000
        months = pd.date_range("2000-01-01", periods=12, freq="MS").astype(str)
        cells = np.arange(ncell, dtype="int64") + 600_000_000_000_000_000
        df = pd.DataFrame(
            {
                "datetime": np.tile(months, ncell),
                "value": np.random.rand(ncell * len(months)),
                "geometry_id": np.repeat(cells, len(months)),
            }
        )
        timed(
            label=f"insert {len(df):,} rows ({ncell:,} cells)",
            func=lambda: db.insert_records(dataframe=df, spec_name="BENCH", flag=1),
        )
        query = {"spec_name": "BENCH", "geometry_id": cells[:40_000]}
        result = timed(
            label="query 40,000 cells",
            func=lambda: db.query_records(query_dict=query),
        )
        db.close()
        self.assertEqual(len(result), 40_000 * len(months))


# ... {develop}

# CLASSES -- Module-level
# =======================================================================
# ... {develop}


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":
    # Script section
    # ===================================================================
    unittest.main()
    # ... {develop}
