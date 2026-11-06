# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for the ``databases`` module.

Features
--------
The test suite verifies that:

* SQL files are resolved in the class ``SQL_DIR`` first, then in ``base/``.
* A child class with a partial SQL folder creates a full database with ``new()``.
* A missing ``.sql`` path raises ``FileNotFoundError`` instead of running as SQL text.
* ``new()`` reads TOML and JSON setup files and respects ``overwrite``.
* Spec names are normalized, validated and unique, in Python and in the schema.
* ``spec_name`` and ``spec_id`` resolve to the same specs; the name wins on conflict.
* Invalid inputs raise clear errors before anything is written: extra columns,
  unknown flags, unparseable dates and specs pointing to unknown catalogue entries.
* Inserts are atomic; ``transaction()`` groups them, rolls back on failure and nests.
* ``query_records`` validates keys, orders rows, reverses the transform and builds
  the wide format and spec metadata.
* ``SemiSpatialDB`` requires ``geometry_id`` on insert, filters by any number of
  ids, and pivots to ``(spec_name, geometry_id)`` columns.
* Domain notation is parsed and checked; NaN values are dropped or stored as
  voids, and out-of-domain values are flagged ``suspect``.

Databases are built once per class in a single temporary folder.

"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import unittest
import json, shutil, sqlite3, tempfile
from pathlib import Path
from unittest import mock

# ... {develop}

# External imports
# =======================================================================
import numpy as np
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
import plans.databases
from plans.databases import DataBase, SemiSpatialDB, DATA_SQL_DIR, _TABLE_ORDER

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

SPECS = [
    {
        "name": "PPT_MONTHLY_CHIRPS",
        "abstract": "Monthly precipitation from CHIRPS v2.0",
        "method": "spatial average",
        "timestep": "1M",
        "extent": "watershed",
        "scale": 1,
        "offset": 0,
        "start": "2000-01-01",
        "end": None,
        "variable_name": "precipitation",
        "statistic_name": "sum",
        "source_name": "CHIRPS v2.0",
    }
]

# raw SQL insert into specs, bypassing Python checks
SQL_INSERT_SPEC = (
    "INSERT INTO specs (name, abstract, method, timestep, extent, start, "
    "variable_name, statistic_name, source_name) "
    "VALUES (?, 'a', 'm', '1M', 'e', 0, 'precipitation', 'sum', 'CHIRPS v2.0')"
)

# ... {develop}

# FUNCTIONS
# ***********************************************************************


# CLASSES
# ***********************************************************************


class TestSqlResolution(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests in this class: create one base and one child database.
        """
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.file_specs = cls.temp_dir / "specs.json"
        cls.file_specs.write_text(json.dumps(SPECS), encoding="utf-8")

        cls.db_base = DataBase(name="base")
        cls.db_base.new(config=cls._config(name="base.db"))
        cls.db_child = SemiSpatialDB(name="child")
        cls.db_child.new(config=cls._config(name="child.db"))

    @classmethod
    def tearDownClass(cls):
        """
        Runs once after all tests in this class.
        """
        cls.db_base.close()
        cls.db_child.close()
        shutil.rmtree(cls.temp_dir)
        return None

    @classmethod
    def _config(cls, name):
        return {
            "database": {"path": str(cls.temp_dir / name)},
            "specs": {"path": str(cls.file_specs)},
        }

    def _columns(self, db, table):
        df = db.query_sql(sql=f"PRAGMA table_info({table})")
        return df["name"].tolist()

    def _tables(self, db):
        df = db.query_sql(sql="SELECT name FROM sqlite_master WHERE type = 'table'")
        return set(df["name"])

    # -------------------------------------------------------------------
    # _sql_path
    # -------------------------------------------------------------------
    def test_sql_path_base(self):
        path = self.db_base._sql_path(table="records")
        self.assertEqual(path, DATA_SQL_DIR / "base" / "records.sql")

    def test_sql_path_child_override(self):
        path = self.db_child._sql_path(table="records")
        self.assertEqual(path, DATA_SQL_DIR / "semispatial" / "records.sql")

    def test_sql_path_child_fallback(self):
        path = self.db_child._sql_path(table="specs")
        self.assertEqual(path, DATA_SQL_DIR / "base" / "specs.sql")

    def test_sql_path_missing_raises(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            self.db_child._sql_path(table="ghost")
        self.assertIn("ghost", str(ctx.exception))

    # -------------------------------------------------------------------
    # new
    # -------------------------------------------------------------------
    def test_new_base_schema(self):
        self.assertTrue(set(_TABLE_ORDER) <= self._tables(db=self.db_base))
        cols = self._columns(db=self.db_base, table="records")
        self.assertNotIn("geometry_id", cols)

    def test_new_child_schema(self):
        # records from semispatial/, all other tables from base/
        self.assertTrue(set(_TABLE_ORDER) <= self._tables(db=self.db_child))
        cols = self._columns(db=self.db_child, table="records")
        self.assertIn("geometry_id", cols)

    # -------------------------------------------------------------------
    # execute_sql and query_sql
    # -------------------------------------------------------------------
    def test_execute_sql_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.db_base.execute_sql(sql=self.temp_dir / "missing.sql")

    def test_query_sql_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.db_base.query_sql(sql=self.temp_dir / "missing.sql")

    def test_execute_sql_file(self):
        file_sql = self.temp_dir / "probe.sql"
        file_sql.write_text("CREATE TABLE probe (id INTEGER);", encoding="utf-8")
        self.db_base.execute_sql(sql=file_sql)
        self.assertIn("probe", self._tables(db=self.db_base))

    def test_query_sql_text(self):
        df = self.db_base.query_sql(sql="SELECT name FROM specs")
        self.assertEqual(df["name"].tolist(), ["PPT_MONTHLY_CHIRPS"])


class TestNew(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests in this class: write a specs file and two setup files.
        """
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.file_specs = cls.temp_dir / "specs.json"
        cls.file_specs.write_text(json.dumps(SPECS), encoding="utf-8")
        cls.file_db = cls.temp_dir / "new.db"
        # forward slashes keep the TOML string free of escapes
        cls.file_toml = cls.temp_dir / "setup.toml"
        cls.file_toml.write_text(
            f'[database]\npath = "{cls.file_db.as_posix()}"\n\n'
            f'[specs]\npath = "{cls.file_specs.as_posix()}"\n',
            encoding="utf-8",
        )
        cls.file_json = cls.temp_dir / "setup.json"
        cls.file_json.write_text(
            json.dumps(
                {
                    "database": {"path": str(cls.file_db)},
                    "specs": {"path": str(cls.file_specs)},
                }
            ),
            encoding="utf-8",
        )

    @classmethod
    def tearDownClass(cls):
        """
        Runs once after all tests in this class.
        """
        shutil.rmtree(cls.temp_dir)
        return None

    def _new(self, config, overwrite):
        db = DataBase(name="new")
        db.new(config=config, overwrite=overwrite)
        names = db.query_sql(sql="SELECT name FROM specs")["name"].tolist()
        db.close()
        return names

    def test_from_toml_and_json(self):
        for config in (self.file_toml, self.file_json):
            with self.subTest(config=config.suffix):
                names = self._new(config=config, overwrite=True)
                self.assertEqual(names, ["PPT_MONTHLY_CHIRPS"])

    def test_overwrite(self):
        self._new(config=self.file_json, overwrite=True)
        with self.assertRaises(FileExistsError):
            self._new(config=self.file_json, overwrite=False)
        # the existing file is kept
        self.assertTrue(self.file_db.exists())

    def test_unsupported_setup_format(self):
        with self.assertRaises(ValueError):
            DataBase.parse_setup(setup=self.temp_dir / "setup.yaml")


class TestSpecNames(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests in this class: create a database with two specs
        (one given in lowercase) and insert records by name and by id.
        """
        cls.temp_dir = Path(tempfile.mkdtemp())
        specs = [
            dict(SPECS[0], name=" ppt_monthly_chirps "),
            dict(SPECS[0], name="Q_2"),
        ]
        cls.file_specs = cls.temp_dir / "specs.json"
        cls.file_specs.write_text(json.dumps(specs), encoding="utf-8")

        cls.db = DataBase(name="specs")
        cls.db.new(config=cls._config(name="specs.db", file_specs=cls.file_specs))

        # 2 records for spec 1 (by name), 3 for spec 2 (by numpy id)
        df = pd.DataFrame(
            {
                "datetime": ["2000-01-01", "2000-02-01", "2000-03-01"],
                "value": [1.0, 2.0, 3.0],
                "flag_value": [1, 1, 1],
            }
        )
        cls.db.insert_records(dataframe=df.head(2), spec_name="ppt_monthly_chirps")
        cls.db.insert_records(dataframe=df, spec_id=np.int64(2))

    @classmethod
    def tearDownClass(cls):
        """
        Runs once after all tests in this class.
        """
        cls.db.close()
        shutil.rmtree(cls.temp_dir)
        return None

    @classmethod
    def _config(cls, name, file_specs):
        return {
            "database": {"path": str(cls.temp_dir / name)},
            "specs": {"path": str(file_specs)},
        }

    def _counts(self, query_dict):
        df = self.db.query_records(query_dict=query_dict)
        return df.groupby("spec_id").size().to_dict()

    # -------------------------------------------------------------------
    # _normalize_spec_name
    # -------------------------------------------------------------------
    def test_normalize_valid(self):
        for name, expected in [
            ("PPT_MONTHLY_CHIRPS", "PPT_MONTHLY_CHIRPS"),
            (" ppt_monthly ", "PPT_MONTHLY"),
            ("Q_2", "Q_2"),
        ]:
            with self.subTest(name=name):
                self.assertEqual(DataBase._normalize_spec_name(name=name), expected)

    def test_normalize_invalid(self):
        for name in ["PPT MONTHLY", "1ABC", "PPT-1", "ÁGUA", "", None]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    DataBase._normalize_spec_name(name=name)

    def test_normalize_whitespace_message(self):
        with self.assertRaises(ValueError) as ctx:
            DataBase._normalize_spec_name(name="ppt monthly")
        self.assertIn("underscores", str(ctx.exception))

    # -------------------------------------------------------------------
    # seeding and uniqueness
    # -------------------------------------------------------------------
    def test_seed_stores_uppercase(self):
        df = self.db.query_sql(sql="SELECT name FROM specs ORDER BY id")
        self.assertEqual(df["name"].tolist(), ["PPT_MONTHLY_CHIRPS", "Q_2"])

    def test_seed_duplicate_raises_and_leaves_no_file(self):
        file_specs = self.temp_dir / "specs_dup.json"
        dups = [dict(SPECS[0], name="A"), dict(SPECS[0], name="a")]
        file_specs.write_text(json.dumps(dups), encoding="utf-8")
        db = DataBase(name="dup")
        with self.assertRaises(ValueError) as ctx:
            db.new(config=self._config(name="dup.db", file_specs=file_specs))
        self.assertIn("'A'", str(ctx.exception))
        self.assertFalse((self.temp_dir / "dup.db").exists())

    def test_insert_row_duplicate_raises(self):
        with self.assertRaises(ValueError):
            self.db.insert_row(row_dict=dict(SPECS[0], name="q_2"), on_table="specs")

    def test_schema_check_rejects_lowercase(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.conn.execute(SQL_INSERT_SPEC, ("ppt",))

    def test_schema_unique_rejects_duplicate(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.conn.execute(SQL_INSERT_SPEC, ("Q_2",))

    # -------------------------------------------------------------------
    # _resolve_spec_ids
    # -------------------------------------------------------------------
    def test_resolve_by_name_lenient(self):
        ids = self.db._resolve_spec_ids(spec_name=["ppt_monthly_chirps", " Q_2"])
        self.assertEqual(ids, [1, 2])

    def test_resolve_by_numpy_id(self):
        ids = self.db._resolve_spec_ids(spec_id=np.array([2, 1]))
        self.assertEqual(ids, [2, 1])

    def test_resolve_name_wins_with_warning(self):
        with self.assertWarns(UserWarning):
            ids = self.db._resolve_spec_ids(spec_name="Q_2", spec_id=1)
        self.assertEqual(ids, [2])

    def test_resolve_none(self):
        with self.assertRaises(ValueError):
            self.db._resolve_spec_ids()
        self.assertIsNone(self.db._resolve_spec_ids(required=False))

    def test_resolve_unknown_name_lists_valid(self):
        with self.assertRaises(ValueError) as ctx:
            self.db._resolve_spec_ids(spec_name="NOPE")
        self.assertIn("PPT_MONTHLY_CHIRPS", str(ctx.exception))

    def test_resolve_unknown_id(self):
        with self.assertRaises(ValueError):
            self.db._resolve_spec_ids(spec_id=9)

    def test_resolve_float_id_raises(self):
        with self.assertRaises(TypeError):
            self.db._resolve_spec_ids(spec_id=1.0)

    # -------------------------------------------------------------------
    # insert and query
    # -------------------------------------------------------------------
    def test_insert_without_spec_raises(self):
        df = pd.DataFrame({"datetime": ["2000-01-01"], "value": [1.0]})
        with self.assertRaises(ValueError):
            self.db.insert_records(dataframe=df, flag=1)

    def test_insert_two_specs_raises(self):
        df = pd.DataFrame({"datetime": ["2000-01-01"], "value": [1.0]})
        with self.assertRaises(ValueError):
            self.db.insert_records(
                dataframe=df, spec_name=["Q_2", "PPT_MONTHLY_CHIRPS"], flag=1
            )

    def test_query_all(self):
        self.assertEqual(self._counts(query_dict={}), {1: 2, 2: 3})

    def test_query_by_name(self):
        self.assertEqual(self._counts(query_dict={"spec_name": "q_2"}), {2: 3})

    def test_query_by_numpy_ids(self):
        counts = self._counts(query_dict={"spec_id": np.array([1, 2])})
        self.assertEqual(counts, {1: 2, 2: 3})

    def test_query_name_wins_with_warning(self):
        with self.assertWarns(UserWarning):
            counts = self._counts(query_dict={"spec_name": "Q_2", "spec_id": 1})
        self.assertEqual(counts, {2: 3})

    # -------------------------------------------------------------------
    # inspect_specs
    # -------------------------------------------------------------------
    def test_inspect_specs_name_first(self):
        output = self.db.inspect_specs(quiet=True)
        self.assertIn("PPT_MONTHLY_CHIRPS  (id 1)", output)


class TestInsertValidation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests in this class: create one database with one spec.
        """
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.db = DataBase(name="validation")
        cls.db.new(config=cls._config(name="validation.db", specs=SPECS))
        cls.df = pd.DataFrame(
            {
                "datetime": ["2000-01-01", "2000-02-01"],
                "value": [1.0, 2.0],
                "flag_value": [1, 1],
            }
        )

    @classmethod
    def tearDownClass(cls):
        """
        Runs once after all tests in this class.
        """
        cls.db.close()
        shutil.rmtree(cls.temp_dir)
        return None

    @classmethod
    def _config(cls, name, specs):
        file_specs = cls.temp_dir / f"{Path(name).stem}.json"
        file_specs.write_text(json.dumps(specs), encoding="utf-8")
        return {
            "database": {"path": str(cls.temp_dir / name)},
            "specs": {"path": str(file_specs)},
        }

    def _count(self):
        return self.db.query_sql(sql="SELECT COUNT(*) AS n FROM records")["n"].item()

    def _assert_rejected(self, dataframe, message, **kwargs):
        # the insert raises with the message and writes nothing
        n0 = self._count()
        with self.assertRaises(ValueError) as ctx:
            self.db.insert_records(
                dataframe=dataframe, spec_name="PPT_MONTHLY_CHIRPS", **kwargs
            )
        self.assertIn(message, str(ctx.exception))
        self.assertEqual(self._count(), n0)

    # -------------------------------------------------------------------
    # records
    # -------------------------------------------------------------------
    def test_unknown_flag(self):
        df = self.df.assign(flag_value=np.array([1, 9]))
        self._assert_rejected(
            dataframe=df, message="Unknown flag_value(s): [9]. Valid: [0, 1, 2]"
        )

    def test_unparseable_dates(self):
        df = self.df.assign(datetime=["2000-01-01", "not a date"])
        self._assert_rejected(dataframe=df, message="1 unparseable date(s)")

    def test_extra_column_raises(self):
        df = self.df.assign(geometry_id=5)
        self._assert_rejected(dataframe=df, message="['geometry_id']")

    def test_extra_column_dropped(self):
        n0 = self._count()
        self.db.insert_records(
            dataframe=self.df.assign(station="A"),
            spec_name="PPT_MONTHLY_CHIRPS",
            drop_extra=True,
        )
        self.assertEqual(self._count(), n0 + 2)

    def test_load_records_drop_extra(self):
        file_csv = self.temp_dir / "wide.csv"
        self.df.assign(station="A").to_csv(file_csv, sep=";", index=False)
        n0 = self._count()
        with self.assertRaises(ValueError) as ctx:
            self.db.load_records(
                files=[file_csv], spec_name="PPT_MONTHLY_CHIRPS", sep=";"
            )
        self.assertIn("['station']", str(ctx.exception))
        self.db.load_records(
            files=[file_csv], spec_name="PPT_MONTHLY_CHIRPS", sep=";", drop_extra=True
        )
        self.assertEqual(self._count(), n0 + 2)

    # -------------------------------------------------------------------
    # specs in new()
    # -------------------------------------------------------------------
    def _assert_new_rejected(self, specs, message):
        # new() raises with the message and leaves no database file
        db = DataBase(name="bad")
        with self.assertRaises(ValueError) as ctx:
            db.new(config=self._config(name="bad.db", specs=specs))
        self.assertIn(message, str(ctx.exception))
        self.assertFalse((self.temp_dir / "bad.db").exists())

    def test_specs_typo_column(self):
        spec = {k: v for k, v in SPECS[0].items() if k != "offset"}
        self._assert_new_rejected(specs=[dict(spec, ofset=1)], message="['ofset']")

    def test_specs_unknown_variable(self):
        spec = dict(SPECS[0], variable_name="rainz")
        self._assert_new_rejected(specs=[spec], message="PPT_MONTHLY_CHIRPS: 'rainz'")

    def test_specs_unparseable_start(self):
        spec = dict(SPECS[0], start="not a date")
        self._assert_new_rejected(specs=[spec], message="in 'start'")


class TestTransactions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests in this class: create one database with specs A, B, C.
        """
        cls.temp_dir = Path(tempfile.mkdtemp())
        file_specs = cls.temp_dir / "specs.json"
        specs = [dict(SPECS[0], name=n) for n in ("A", "B", "C")]
        file_specs.write_text(json.dumps(specs), encoding="utf-8")
        cls.file_db = cls.temp_dir / "tx.db"
        cls.db = DataBase(name="tx")
        cls.db.new(
            config={
                "database": {"path": str(cls.file_db)},
                "specs": {"path": str(file_specs)},
            }
        )
        cls.good = pd.DataFrame(
            {
                "datetime": ["2000-01-01", "2000-02-01", "2000-03-01"],
                "value": [1.0, 2.0, 3.0],
                "flag_value": [1, 1, 1],
            }
        )
        cls.bad = cls.good.assign(flag_value=[1, 1, 9])

    @classmethod
    def tearDownClass(cls):
        """
        Runs once after all tests in this class.
        """
        cls.db.close()
        shutil.rmtree(cls.temp_dir)
        return None

    def setUp(self):
        # each test starts from an empty records table
        self.db.conn.execute("DELETE FROM records")
        self.db.conn.commit()

    def _committed(self):
        # count rows as seen by another connection (committed rows only)
        with sqlite3.connect(self.file_db) as conn:
            n = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        conn.close()
        return n

    def test_single_insert_commits(self):
        self.db.insert_records(dataframe=self.good, spec_name="A")
        self.assertEqual(self._committed(), 3)
        self.assertFalse(self.db.conn.in_transaction)

    def test_single_insert_atomic_across_chunks(self):
        # the database rejects the last row (unknown flag) after earlier chunks went in
        df = pd.DataFrame(
            {
                "datetime": [1, 2, 3, 4, 5],
                "value": [1.0] * 5,
                "flag_value": [1, 1, 1, 1, 5],
                "spec_id": [1] * 5,
            }
        )
        with mock.patch.object(plans.databases, "_CHUNK_SIZE", 2):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.insert_rows(dataframe=df, on_table="records")
        self.assertEqual(self._committed(), 0)
        self.assertFalse(self.db.conn.in_transaction)

    def test_block_rolls_back_all(self):
        with self.assertRaises(ValueError):
            with self.db.transaction():
                self.db.insert_records(dataframe=self.good, spec_name="A")
                self.db.insert_records(dataframe=self.good, spec_name="B")
                self.db.insert_records(dataframe=self.bad, spec_name="C")
        self.assertEqual(self._committed(), 0)
        self.assertFalse(self.db.conn.in_transaction)

    def test_block_commits_at_end(self):
        with self.db.transaction():
            self.db.insert_records(dataframe=self.good, spec_name="A")
            # not visible to other connections until the block ends
            self.assertEqual(self._committed(), 0)
            self.db.insert_records(dataframe=self.good, spec_name="B")
        self.assertEqual(self._committed(), 6)

    def test_nested_inner_failure(self):
        with self.db.transaction():
            self.db.insert_records(dataframe=self.good, spec_name="A")
            with self.assertRaises(RuntimeError):
                with self.db.transaction():
                    self.db.insert_records(dataframe=self.good, spec_name="B")
                    raise RuntimeError("inner fails")
            self.db.insert_records(dataframe=self.good, spec_name="C")
        df = self.db.query_records(query_dict={"spec_name": ["A", "B", "C"]})
        self.assertEqual(df.groupby("spec_id").size().to_dict(), {1: 3, 3: 3})
        self.assertEqual(self._committed(), 6)

    def test_replicates_stored_twice(self):
        # no uniqueness on records, by design
        self.db.insert_records(dataframe=self.good, spec_name="A")
        self.db.insert_records(dataframe=self.good, spec_name="A")
        self.assertEqual(self._committed(), 6)


class TestQueryRecords(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests in this class: create specs B_SECOND (id 1) and
        A_FIRST (id 2, with a transform), insert out of order, with one replicate.
        """
        cls.temp_dir = Path(tempfile.mkdtemp())
        file_specs = cls.temp_dir / "specs.json"
        specs = [
            dict(SPECS[0], name="B_SECOND"),
            dict(
                SPECS[0],
                name="A_FIRST",
                scale=10,
                offset=5,
                variable_name="streamflow",
                source_name="ANA",
            ),
        ]
        file_specs.write_text(json.dumps(specs), encoding="utf-8")
        cls.db = DataBase(name="query")
        cls.db.new(
            config={
                "database": {"path": str(cls.temp_dir / "query.db")},
                "specs": {"path": str(file_specs)},
            }
        )
        cls.db.insert_records(
            dataframe=pd.DataFrame(
                {
                    "datetime": ["2000-01-03", "2000-01-01", "2000-01-02"],
                    "value": [3.0, 1.0, 2.0],
                }
            ),
            spec_name="A_FIRST",
            flag=1,
        )
        # B_SECOND has a replicate at 2000-01-01 (10 and 30)
        cls.db.insert_records(
            dataframe=pd.DataFrame(
                {
                    "datetime": ["2000-01-02", "2000-01-01", "2000-01-01"],
                    "value": [20.0, 10.0, 30.0],
                }
            ),
            spec_name="B_SECOND",
            flag=1,
        )

    @classmethod
    def tearDownClass(cls):
        """
        Runs once after all tests in this class.
        """
        cls.db.close()
        shutil.rmtree(cls.temp_dir)
        return None

    def _query(self, query_dict):
        return self.db.query_records(query_dict=query_dict)

    # -------------------------------------------------------------------
    # keys
    # -------------------------------------------------------------------
    def test_unknown_key_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self._query(query_dict={"variable_name": "precipitation"})
        self.assertIn("variable_name", str(ctx.exception))

    def test_aggfunc_without_wide_raises(self):
        with self.assertRaises(ValueError):
            self._query(query_dict={"aggfunc": "mean"})

    def test_numpy_flag_value(self):
        df = self._query(query_dict={"flag_value": np.int64(1)})
        self.assertEqual(len(df), 6)
        df = self._query(query_dict={"flag_value": np.array([0])})
        self.assertEqual(len(df), 0)

    # -------------------------------------------------------------------
    # long format
    # -------------------------------------------------------------------
    def test_long_order_and_spec_name(self):
        df = self._query(query_dict={})
        self.assertEqual(df["spec_name"].tolist(), ["B_SECOND"] * 3 + ["A_FIRST"] * 3)
        self.assertEqual(df["spec_id"].tolist(), [1, 1, 1, 2, 2, 2])
        self.assertTrue(df.groupby("spec_id")["datetime"].is_monotonic_increasing.all())
        # replicates keep insertion order
        self.assertEqual(df["value"].tolist()[:2], [10.0, 30.0])

    def test_transform_round_trip(self):
        df = self._query(query_dict={"spec_name": "A_FIRST"})
        self.assertEqual(df["value"].tolist(), [1.0, 2.0, 3.0])
        raw = self._query(
            query_dict={"spec_name": "A_FIRST", "transform_values": False}
        )
        # stored = actual * scale + offset
        self.assertEqual(raw["value"].tolist(), [15.0, 25.0, 35.0])

    def test_with_meta_long(self):
        df = self._query(query_dict={"spec_name": "A_FIRST", "with_meta": True})
        self.assertEqual(set(df["variable_name"]), {"streamflow"})
        self.assertEqual(set(df["source_name"]), {"ANA"})
        self.assertIn("units", df.columns)

    # -------------------------------------------------------------------
    # wide format
    # -------------------------------------------------------------------
    def test_wide_unique(self):
        df = self._query(query_dict={"spec_name": "A_FIRST", "wide": True})
        self.assertEqual(df.columns.tolist(), ["A_FIRST"])
        self.assertEqual(df.index.name, "datetime")
        self.assertEqual(df["A_FIRST"].tolist(), [1.0, 2.0, 3.0])

    def test_wide_replicates_raise(self):
        with self.assertRaises(ValueError) as ctx:
            self._query(query_dict={"wide": True})
        self.assertIn("B_SECOND", str(ctx.exception))
        self.assertIn("has 2 values", str(ctx.exception))

    def test_wide_aggfunc(self):
        df = self._query(query_dict={"wide": True, "aggfunc": "mean"})
        # columns follow spec order, not alphabetical order
        self.assertEqual(df.columns.tolist(), ["B_SECOND", "A_FIRST"])
        self.assertEqual(df["B_SECOND"].tolist()[:2], [20.0, 20.0])
        self.assertTrue(np.isnan(df["B_SECOND"].iloc[2]))

    def test_with_meta_wide(self):
        df = self._query(query_dict={"wide": True, "aggfunc": "max", "with_meta": True})
        meta = df.attrs["specs"]
        self.assertEqual(meta["spec_name"].tolist(), df.columns.tolist())
        self.assertEqual(
            meta["variable_name"].tolist(), ["precipitation", "streamflow"]
        )


class TestSemiSpatialDB(unittest.TestCase):

    # H3-sized ids: 3 small cells and 33,000 cells, above the SQLite parameter cap
    CELLS = np.array([3, 1, 2], dtype="int64") + 600_000_000_000_000_000
    MANY = np.arange(33_000, dtype="int64") + 700_000_000_000_000_000

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests in this class: create a semispatial database with
        3 cells x 2 months in spec CELLS and 33,000 cells x 1 month in spec MANY.
        """
        cls.temp_dir = Path(tempfile.mkdtemp())
        file_specs = cls.temp_dir / "specs.json"
        specs = [dict(SPECS[0], name="CELLS"), dict(SPECS[0], name="MANY")]
        file_specs.write_text(json.dumps(specs), encoding="utf-8")
        cls.db = SemiSpatialDB(name="semi")
        cls.db.new(
            config={
                "database": {"path": str(cls.temp_dir / "semi.db")},
                "specs": {"path": str(file_specs)},
            }
        )
        # value = cell position * 10 + month
        cls.db.insert_records(
            dataframe=pd.DataFrame(
                {
                    "datetime": ["2000-01-01", "2000-02-01"] * 3,
                    "value": [11.0, 12.0, 21.0, 22.0, 31.0, 32.0],
                    "geometry_id": np.repeat(cls.CELLS, 2),
                }
            ),
            spec_name="CELLS",
            flag=1,
        )
        cls.db.insert_records(
            dataframe=pd.DataFrame(
                {"datetime": "2000-01-01", "value": 1.0, "geometry_id": cls.MANY}
            ),
            spec_name="MANY",
            flag=1,
        )

    @classmethod
    def tearDownClass(cls):
        """
        Runs once after all tests in this class.
        """
        cls.db.close()
        shutil.rmtree(cls.temp_dir)
        return None

    def _query(self, query_dict):
        return self.db.query_records(query_dict=query_dict)

    # -------------------------------------------------------------------
    # schema and insert
    # -------------------------------------------------------------------
    def test_geometry_index_exists(self):
        df = self.db.query_sql(sql="PRAGMA index_list(records)")
        self.assertIn("idx_records_spec_geometry_datetime", df["name"].tolist())

    def test_insert_missing_geometry_id(self):
        df = pd.DataFrame({"datetime": ["2000-01-01"], "value": [1.0]})
        with self.assertRaises(ValueError) as ctx:
            self.db.insert_records(dataframe=df, spec_name="CELLS", flag=1)
        self.assertIn("geometry_id", str(ctx.exception))

    def test_inspect_records(self):
        output = self.db.inspect_records(head=2, tail=2, quiet=True)
        self.assertIn("geometry_id", output)

    # -------------------------------------------------------------------
    # query
    # -------------------------------------------------------------------
    def test_filter_small_list(self):
        ids = self.CELLS[:2].tolist()
        df = self._query(query_dict={"spec_name": "CELLS", "geometry_id": ids})
        self.assertEqual(set(df["geometry_id"]), set(ids))
        self.assertEqual(len(df), 4)

    def test_filter_numpy_scalar(self):
        df = self._query(query_dict={"geometry_id": self.CELLS[0]})
        self.assertEqual(df["value"].tolist(), [11.0, 12.0])

    def test_filter_above_parameter_cap(self):
        df = self._query(query_dict={"spec_name": "MANY", "geometry_id": self.MANY})
        self.assertEqual(len(df), len(self.MANY))

    def test_long_order(self):
        df = self._query(query_dict={"spec_name": "CELLS"})
        # ordered by geometry_id, then datetime
        self.assertEqual(df["value"].tolist(), [21.0, 22.0, 31.0, 32.0, 11.0, 12.0])

    def test_wide_multiindex(self):
        df = self._query(query_dict={"spec_name": "CELLS", "wide": True})
        self.assertEqual(df.columns.names, ["spec_name", "geometry_id"])
        self.assertEqual(df.shape, (2, 3))
        self.assertEqual(df[("CELLS", int(self.CELLS[0]))].tolist(), [11.0, 12.0])

    def test_wide_replicates(self):
        # a replicate in one cell raises without aggfunc; removed afterwards
        row = {"datetime": "2000-01-01", "value": 13.0, "geometry_id": self.CELLS[0]}
        self.db.insert_record(row_dict=row, spec_name="CELLS", flag=1)
        try:
            with self.assertRaises(ValueError):
                self._query(query_dict={"spec_name": "CELLS", "wide": True})
            df = self._query(
                query_dict={"spec_name": "CELLS", "wide": True, "aggfunc": "mean"}
            )
            self.assertEqual(df[("CELLS", int(self.CELLS[0]))].iloc[0], 12.0)
        finally:
            self.db.conn.execute("DELETE FROM records WHERE value = 13.0")
            self.db.conn.commit()


class TestDomain(unittest.TestCase):

    def test_parse_valid(self):
        inf = np.inf
        for domain, expected in [
            ("[0U)", [(0.0, inf, True, False)]),
            ("(0U1]", [(0.0, 1.0, False, True)]),
            ("[-273.15U)", [(-273.15, inf, True, False)]),
            ("(U)", [(-inf, inf, False, False)]),
            ("[5U5]", [(5.0, 5.0, True, True)]),
            (
                "[-90U-60]U[60U90]",
                [(-90.0, -60.0, True, True), (60.0, 90.0, True, True)],
            ),
            (" [0U1] U (5U) ", [(0.0, 1.0, True, True), (5.0, inf, False, False)]),
        ]:
            with self.subTest(domain=domain):
                self.assertEqual(DataBase._parse_domain(domain=domain), expected)

    def test_parse_invalid(self):
        for domain in [
            "",
            "0U1",
            "[0,1]",
            "[0U1]U",
            "(0U)(1U2)",
            "[aU1]",
            "[2U1]",
            "(5U5]",
        ]:
            with self.subTest(domain=domain):
                with self.assertRaises(ValueError):
                    DataBase._parse_domain(domain=domain)

    def test_in_domain(self):
        v = np.array([-100, -90, -60, -59, 0, 60, 90, 91, np.nan])
        inside = DataBase._in_domain(values=v, domain="[-90U-60]U[60U90]")
        self.assertEqual(inside.tolist(), [0, 1, 1, 0, 0, 1, 1, 0, 0])
        inside = DataBase._in_domain(values=np.array([0.0, 0.5, 1.0]), domain="(0U1]")
        self.assertEqual(inside.tolist(), [0, 1, 1])


class TestVoidAndSuspect(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests in this class: create one database with spec PPT
        (precipitation, domain [0U)) and spec SHIFT (offset -100, so stored and
        actual values differ in sign).
        """
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.file_specs = cls.temp_dir / "specs.json"
        specs = [dict(SPECS[0], name="PPT"), dict(SPECS[0], name="SHIFT", offset=-100)]
        cls.file_specs.write_text(json.dumps(specs), encoding="utf-8")
        cls.db = DataBase(name="flags")
        cls.db.new(config=cls._config(name="flags.db"))

    @classmethod
    def tearDownClass(cls):
        """
        Runs once after all tests in this class.
        """
        cls.db.close()
        shutil.rmtree(cls.temp_dir)
        return None

    @classmethod
    def _config(cls, name, catalogs=None):
        config = {
            "database": {"path": str(cls.temp_dir / name)},
            "specs": {"path": str(cls.file_specs)},
        }
        if catalogs:
            config["catalogs"] = catalogs
        return config

    def setUp(self):
        # each test starts from an empty records table
        self.db.conn.execute("DELETE FROM records")
        self.db.conn.commit()

    def _insert(self, values, **kwargs):
        dates = pd.date_range("2000-01-01", periods=len(values), freq="D").astype(str)
        df = pd.DataFrame({"datetime": dates, "value": values})
        kwargs.setdefault("spec_name", "PPT")
        kwargs.setdefault("flag", 1)
        self.db.insert_records(dataframe=df, **kwargs)

    def _stored(self):
        # raw rows, as SQLite holds them
        return self.db.conn.execute(
            "SELECT value, flag_value FROM records ORDER BY datetime"
        ).fetchall()

    # -------------------------------------------------------------------
    # nan_policy
    # -------------------------------------------------------------------
    def test_nan_dropped_by_default(self):
        self._insert(values=[1.0, np.nan, 3.0])
        self.assertEqual(self._stored(), [(1.0, 1), (3.0, 1)])

    def test_nan_void(self):
        self._insert(values=[1.0, np.nan], nan_policy="void")
        # NULL value with the void flag, overriding the batch flag
        self.assertEqual(self._stored(), [(1.0, 1), (None, 0)])
        df = self.db.query_records(query_dict={"spec_name": "PPT"})
        self.assertTrue(np.isnan(df["value"].iloc[1]))
        self.assertEqual(df["flag_value"].tolist(), [1, 0])

    def test_nan_void_with_transform(self):
        self._insert(values=[np.nan], spec_name="SHIFT", nan_policy="void")
        self.assertEqual(self._stored(), [(None, 0)])

    def test_nan_policy_invalid(self):
        with self.assertRaises(ValueError):
            self._insert(values=[1.0], nan_policy="fill")

    def test_schema_rejects_null_regular(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.conn.execute(
                "INSERT INTO records (datetime, value, flag_value, spec_id) "
                "VALUES (0, NULL, 1, 1)"
            )
        self.db.conn.rollback()

    def test_wide_mean_skips_void(self):
        df = pd.DataFrame(
            {"datetime": ["2000-01-01"] * 2, "value": [2.0, np.nan], "flag_value": 1}
        )
        self.db.insert_records(dataframe=df, spec_name="PPT", nan_policy="void")
        wide = self.db.query_records(
            query_dict={"spec_name": "PPT", "wide": True, "aggfunc": "mean"}
        )
        self.assertEqual(wide["PPT"].tolist(), [2.0])

    # -------------------------------------------------------------------
    # domain check
    # -------------------------------------------------------------------
    def test_out_of_domain_suspect(self):
        with self.assertWarns(UserWarning) as ctx:
            self._insert(values=[1.0, -1.0, 0.0])
        self.assertIn("1 value(s) of PPT outside [0U)", str(ctx.warning))
        # the value is kept; only the flag changes
        self.assertEqual(self._stored(), [(1.0, 1), (-1.0, 2), (0.0, 1)])

    def test_given_flags_kept(self):
        df = pd.DataFrame(
            {"datetime": ["2000-01-01"], "value": [-1.0], "flag_value": [0]}
        )
        self.db.insert_records(dataframe=df, spec_name="PPT")
        self.assertEqual(self._stored(), [(-1.0, 0)])

    def test_check_domain_off(self):
        self._insert(values=[-1.0], check_domain=False)
        self.assertEqual(self._stored(), [(-1.0, 1)])

    def test_domain_on_actual_values(self):
        # actual 50 is stored as -50 (offset -100) and stays regular
        self._insert(values=[50.0], spec_name="SHIFT")
        self.assertEqual(self._stored(), [(-50.0, 1)])

    # -------------------------------------------------------------------
    # catalogs
    # -------------------------------------------------------------------
    def test_bad_domain_fails_creation(self):
        file_vars = self.temp_dir / "variables_bad.csv"
        df = pd.read_csv(self.db.variables_default, sep=";")
        df.loc[0, "domain"] = "(0,1)"
        df.to_csv(file_vars, sep=";", index=False)
        db = DataBase(name="bad")
        config = self._config(name="bad.db", catalogs={"variables": str(file_vars)})
        with self.assertRaises(ValueError) as ctx:
            db.new(config=config)
        self.assertIn("precipitation", str(ctx.exception))
        self.assertFalse((self.temp_dir / "bad.db").exists())

    def test_no_suspect_flag_skips_check(self):
        file_flags = self.temp_dir / "flags_old.csv"
        df = pd.read_csv(self.db.flags_default, sep=";")
        df[df["name"] != "suspect"].to_csv(file_flags, sep=";", index=False)
        db = DataBase(name="old")
        db.new(config=self._config(name="old.db", catalogs={"flags": str(file_flags)}))
        df = pd.DataFrame({"datetime": ["2000-01-01"], "value": [-1.0]})
        with self.assertWarns(UserWarning) as ctx:
            db.insert_records(dataframe=df, spec_name="PPT", flag=1)
        db.close()
        self.assertIn("domain check skipped", str(ctx.warning))


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
