# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
SQLite-based database classes for storing and managing hydro-environmental time series.

The base class :class:`DataBase` structures a database around two table categories:
*catalogue* tables (``variables``, ``flags``, ``sources``, ``statistics``) seeded from
shipped CSV files, and *operational* tables (``specs``, ``records``) populated per project.
:class:`SemiSpatialDB` adds a ``feature_id`` to every record, for statistics on
regular grids whose features are kept outside the database.
:class:`SpatialDB` is a GeoPackage file that also holds the features, in a
``features`` layer of any geometry type. Its children :class:`ZonesDB`,
:class:`PathsDB` and :class:`SitesDB` accept polygons, lines or points only,
and records point to them by ``zone_id``, ``path_id`` or ``site_id``.
:class:`SitesDB` branches into :class:`FieldDB` (in situ measurements) and
:class:`LabDB` (laboratory analyses of samples taken at the sites).

Table and column names are lowercase words joined by ``_``; tables are plural,
and a foreign key is the singular table name plus the target column
(``variable_name`` points to ``variables.name``). In :class:`SemiSpatialDB`,
``feature_id`` is the exception: it points to features outside the database.

A new database is created from a TOML (or JSON) setup file::

    [database]
    path = "hydro.db"

    [specs]
    path = "my_specs.json"      # .csv also accepted; format inferred from extension

    [catalogs]                  # optional overrides; omitted keys fall back to defaults
    variables = "my_vars.csv"

The ``specs`` table describes every dataset stored in ``records``.
A JSON specs file is a list of objects, one per dataset::

    [
      {
        "name": "PPT_MONTHLY_CHIRPS",
        "abstract": "Monthly precipitation from CHIRPS v2.0",
        "method": "spatial average over watershed",
        "timestep": "1M",
        "extent": "watershed",
        "scale": 1,
        "offset": 0,
        "start": "1995-01-01",
        "end": null,
        "variable_name": "precipitation",
        "statistic_name": "sum",
        "source_name": "CHIRPS v2.0"
      }
    ]

Spec names are unique and uppercase (ASCII letters, digits and ``_``, starting
with a letter), so they never read like column names. Input names are stripped
and uppercased, so ``ppt_monthly_chirps`` resolves to ``PPT_MONTHLY_CHIRPS``.
Public methods take ``spec_name`` (preferred) or ``spec_id``; ids are only
stable inside one database file.

Values in ``records`` are stored as ``stored = actual * scale + offset`` and
returned as ``actual = (stored - offset) / scale``. The ``records`` table has no
uniqueness constraint on purpose: replicates at the same datetime are valid
data (eg, three lab analyses on one day). Preventing a batch from being loaded
twice is the job of the ingestion script, not of the database.

Each insert call is atomic and commits on its own. Several calls are grouped
into one all-or-nothing block with :meth:`DataBase.transaction`::

    with db.transaction():
        for name, df in batches.items():
            db.insert_records(dataframe=df, spec_name=name, flag=1)

Every record carries a flag from the ``flags`` table. By default, NaN values
are not stored. With ``nan_policy="void"`` they are stored as NULL with the
``void`` flag (0), so a gap reported by the source can be told apart from data
that was never loaded; NULL is the only placeholder, so SQL aggregates and
pandas skip voids without extra handling. On insert, values outside the
variable domain turn ``regular`` (1) rows into ``suspect`` (2): the value is
kept, and a warning reports the count.

Flags of value 0 or below mean "no measured value" (void, not analysed,
not applicable, not detected, ...) and are the only ones that allow a NULL
value; ``nondetect`` may instead hold the detection limit. Positive flags
always carry a value (regular, suspect, raw, consisted). Censored records
hold a limit, not a measurement, so analyses should filter by flag
(eg, ``"flag_value": [1, 4]``) rather than average everything.

Domain notation
---------------
The ``domain`` column of ``variables`` holds the valid range of actual values
as one or more intervals joined by ``U`` (union). Inside an interval, ``U``
separates the lower and upper bounds. ``[`` and ``]`` include the bound,
``(`` and ``)`` exclude it, and an empty bound is unbounded.

==========================  =========================================  ======================
Notation                    Values accepted                            Example use
==========================  =========================================  ======================
``[0U)``                    ``0 <= x``                                 precipitation
``(0U)``                    ``0 < x``                                  strictly positive
``[0U1]``                   ``0 <= x <= 1``                            fractions
``[-1U1]``                  ``-1 <= x <= 1``                           NDVI
``(0U1]``                   ``0 < x <= 1``                             relative humidity
``[-273.15U)``              ``-273.15 <= x``                           temperature in C
``(U)``                     any value                                  no constraint
``[5U5]``                   ``x == 5``                                 a single point
``[-90U-60]U[60U90]``       ``-90 <= x <= -60`` or ``60 <= x <= 90``   polar latitudes
==========================  =========================================  ======================

Domains are checked when the ``variables`` table is seeded, so a malformed
domain fails at database creation.
"""


# todo next steps

"""
Done: DataBase(), SemiSpatialDB() (feature_id, features outside),
SpatialDB() (GeoPackage, any geometry in a features layer) and its
children ZonesDB(), PathsDB(), SitesDB() (zone_id, path_id, site_id).

Do not rebuild the layer with plain SQL: it removes the GDAL
triggers and rtree index.
See prompts/new_features_ideas/plans_databases.md, section 10.

FieldDB() (SitesDB for in situ data; no changes yet).
LabDB() (sites -> samples -> mixtures -> records; no aliquot table),
see prompts/new_features_ideas/plans_databases_sites.md

Next: loaders for the lab results tables (glossary "Fields" rows),
a standards table for thresholds (classes, baselines).

Older roadmap notes:
SitesDB() evolves over more applied cases like station-based data

FieldDB()
-- In situ data generated in the field
---- ClimateDB()
---- RainDB()

---- HydroDB() this one includes other table with the basins

LabDB() 
-- In situ data sampled in the field but generated in the Lab
More complex schema.
To be developed
"""


# IMPORTS
# ***********************************************************************
# Native imports
# =======================================================================
import sqlite3
import tomllib
import json
import time
import re
import operator
import warnings
from contextlib import contextmanager
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
import numpy as np
import pandas as pd
import geopandas as gpd

# ... {develop}

# Project-level imports
# =======================================================================
from plans.root import MbaE
from plans.config import DATA_DIR, DATA_CATALOGS_DIR

DATA_SQL_DIR = DATA_DIR / "sql"

# table creation order respects foreign key dependencies
_TABLE_ORDER = ("variables", "flags", "sources", "statistics", "specs", "records")

# columns that must be converted from text to integer epoch seconds before insert
_EPOCH_COLS = {
    "specs": ("start", "end"),
    "samples": ("datetime",),
}

# rows per executemany call in inserts
_CHUNK_SIZE = 100_000

# domains: one or more intervals like [0U) joined by U; bounds are plain numbers
_BOUND = r"[^\[\]()U\s]*"
_INTERVAL_PATTERN = re.compile(rf"([\[(])\s*({_BOUND})\s*U\s*({_BOUND})\s*([\])])")
_ONE_INTERVAL = rf"[\[(]\s*{_BOUND}\s*U\s*{_BOUND}\s*[\])]"
_DOMAIN_PATTERN = re.compile(rf"\s*{_ONE_INTERVAL}(?:\s*U\s*{_ONE_INTERVAL})*\s*")

# spec names: uppercase ASCII letters, digits and _, starting with a letter
_SPEC_NAME_PATTERN = re.compile(r"[A-Z][A-Z0-9_]*")


class DataBase(MbaE):
    """
    Base SQLite database with a structured schema.

    Manages catalogue and operational tables for hydro-environmental datasets.
    Child classes set :attr:`SQL_DIR` to a folder holding only the ``.sql``
    files that differ (the rest is found in the parents' folders, down to
    ``base/``), extend the class attributes that describe the tables and
    ``records`` (tables, required columns, query keys, row order, wide
    columns), and override methods where the schema diverges.

    :param name: database name
    :type name: str
    :param alias: short alias
    :type alias: str, optional
    """

    # this is /src/plans/data/sql/base
    SQL_DIR = DATA_SQL_DIR / "base"

    # new(): tables in creation order (foreign key dependencies)
    _TABLES = _TABLE_ORDER

    # insert_records: columns the input data must carry (flag_value aside)
    _RECORD_COLUMNS = ("datetime", "value")

    # query_records: accepted keys, row order and wide-format column keys
    _QUERY_KEYS = (
        "spec_name",
        "spec_id",
        "start",
        "end",
        "flag_value",
        "transform_values",
        "wide",
        "aggfunc",
        "with_meta",
    )
    _ORDER_BY = ("spec_id", "datetime")
    _WIDE_COLUMNS = ("spec_name",)
    # query_records: time filtered by start/end, epoch columns returned as
    # datetimes, and the wide-format index
    _TIME_SQL = "r.datetime"
    _EPOCH_OUTPUT = ("datetime", "inserted")
    _WIDE_INDEX = "datetime"

    def __init__(self, name, alias=None):
        super().__init__(name, alias)

        # default catalogue files shipped with the package
        self.variables_default = DATA_CATALOGS_DIR / "variables.csv"
        self.flags_default = DATA_CATALOGS_DIR / "flags.csv"
        self.statistics_default = DATA_CATALOGS_DIR / "statistics.csv"
        self.sources_default = DATA_CATALOGS_DIR / "sources.csv"

        self.conn = None  # active sqlite3.Connection
        self._tx_depth = 0  # open transaction() blocks

    def connect(self, file_db):
        """
        Open a connection to a SQLite database file.

        Enables foreign key enforcement on the connection.

        :param file_db: path to the SQLite file
        :type file_db: str or Path
        :return: active connection
        :rtype: sqlite3.Connection
        """
        self.conn = sqlite3.connect(database=file_db)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._tx_depth = 0
        return self.conn

    def close(self):
        """
        Close the active connection and release the file lock.

        Sets :attr:`conn` to ``None`` after closing.

        :return: None
        :rtype: None
        """
        if self.conn is not None:
            self.conn.close()
            self.conn = None
        return None

    def inspect_schema(self, table=None, quiet=False):
        """
        Print an overview of the database to stdout.

        Without arguments, all tables are rendered three per row in a fixed
        display order: operational tables first (``records``, ``specs``,
        ``flags``), then catalogue tables (``variables``, ``statistics``,
        ``sources``). When ``table`` is given, only that table is shown.
        Each block shows the table name, row count, and column names with types.
        Requires an active connection.

        :param table: name of a single table to inspect; if ``None`` all tables are shown
        :type table: str, optional
        :param quiet: if ``True``, suppress printing and only return the string
        :type quiet: bool
        :return: formatted schema string
        :rtype: str
        """
        _order = (
            (table,)
            if table is not None
            else ("records", "specs", "flags", "variables", "statistics", "sources")
        )

        # build a text block for each table
        blocks = []
        for t in _order:
            count = self.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            cols = self.conn.execute(f"PRAGMA table_info({t})").fetchall()
            block = [f"  {t}  ({count} rows)"]
            for col in cols:
                block.append(f"    {col[1]:<20} {col[2]}")
            blocks.append(block)

        lines = [f"[{self.name}]"]
        if table is not None:
            lines.extend(blocks[0])
            lines.append("")
        else:
            col_width = 36
            for i in range(0, len(blocks), 3):
                group = blocks[i : i + 3]
                height = max(len(b) for b in group)
                group = [b + [""] * (height - len(b)) for b in group]
                for row in zip(*group):
                    lines.append("".join(f"{cell:<{col_width}}" for cell in row))
                lines.append("")

        output = "\n".join(lines)
        if not quiet:
            print(output)
        return output

    def inspect_specs(self, quiet=False):
        """
        Print a summary of all specs defined in the database.

        Each spec is shown as a compact card with its identifying fields,
        time range, linear transform parameters, and abstract.
        Requires an active connection.

        :param quiet: if ``True``, suppress printing and only return the string
        :type quiet: bool
        :return: formatted specs string
        :rtype: str
        """
        rows = self.conn.execute(
            "SELECT id, name, abstract, method, timestep, extent, "
            "scale, offset, start, end, "
            "variable_name, statistic_name, source_name FROM specs"
        ).fetchall()
        lines = [f"[{self.name} — specs]"]
        if not rows:
            lines.append("  (no specs defined)")
        else:
            for row in rows:
                (
                    sid,
                    name,
                    abstract,
                    method,
                    timestep,
                    extent,
                    scale,
                    offset,
                    start,
                    end,
                    variable_name,
                    statistic_name,
                    source_name,
                ) = row
                start_str = pd.Timestamp(start, unit="s", tz="UTC").strftime("%Y-%m-%d")
                end_str = (
                    pd.Timestamp(end, unit="s", tz="UTC").strftime("%Y-%m-%d")
                    if end
                    else "open"
                )
                lines.append("")
                lines.append(f"  {name}  (id {sid})")
                lines.append(
                    f"       {variable_name} · {statistic_name} · {timestep} · {extent}"
                )
                lines.append(f"       source: {source_name}")
                lines.append(f"       period: {start_str} → {end_str}")
                if scale != 1 or offset != 0:
                    lines.append(
                        f"       transform: stored = actual * {scale} + {offset}"
                    )
                lines.append(f"       method: {method}")
                if abstract:
                    lines.append(f"       {abstract}")
        lines.append("")
        output = "\n".join(lines)
        if not quiet:
            print(output)
        return output

    def inspect_records(self, head=10, tail=None, quiet=False):
        """
        Inspect the ``records`` table.

        Always includes the table schema. Then shows the first ``head`` rows
        and/or the last ``tail`` rows with human-readable timestamps.
        Set either to ``None`` to skip that section.
        Requires an active connection.

        :param head: number of rows to show from the top; ``None`` skips
        :type head: int, optional
        :param tail: number of rows to show from the bottom; ``None`` skips
        :type tail: int, optional
        :param quiet: if ``True``, suppress printing and only return the string
        :type quiet: bool
        :return: formatted records string
        :rtype: str
        """
        lines = [self.inspect_schema(table="records", quiet=True)]
        if head is not None:
            df = pd.read_sql(sql=f"SELECT * FROM records LIMIT {head}", con=self.conn)
            lines.append(f"  head ({head})")
            lines.append(self._fmt_records(df=df).to_string(index=False))
            lines.append("")
        if tail is not None:
            df = pd.read_sql(
                sql=f"SELECT * FROM (SELECT * FROM records ORDER BY id DESC LIMIT {tail}) ORDER BY id ASC",
                con=self.conn,
            )
            lines.append(f"  tail ({tail})")
            lines.append(self._fmt_records(df=df).to_string(index=False))
            lines.append("")
        output = "\n".join(lines)
        if not quiet:
            print(output)
        return output

    @staticmethod
    def _fmt_records(df):
        # convert epoch integer columns to readable UTC strings for display
        df = df.copy()
        for col in ("datetime", "inserted"):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], unit="s", utc=True).dt.strftime(
                    "%Y-%m-%d %H:%M"
                )
        return df

    @staticmethod
    def _read_sql(sql):
        # return SQL text from a string or a .sql file path; a missing .sql file raises
        path = Path(sql)
        if path.suffix == ".sql":
            if not path.is_file():
                raise FileNotFoundError(f"SQL file not found: {path}")
            return path.read_text(encoding="utf-8")
        return str(sql)

    def _sql_path(self, table):
        # resolve the table's .sql file along the class hierarchy, child first
        folders = []
        for cls in type(self).__mro__:
            folder = vars(cls).get("SQL_DIR")
            if folder is not None and folder not in folders:
                folders.append(folder)
        for folder in folders:
            path = folder / f"{table}.sql"
            if path.is_file():
                return path
        raise FileNotFoundError(
            f"No SQL file for table {table!r} in {[str(f) for f in folders]}"
        )

    def _create_table(self, table):
        # run the table's .sql file; children override to fill templates
        self.execute_sql(sql=self._sql_path(table=table))

    def _prepare_file(self, cfg, file_db):
        # hook for new(): runs before the connection opens; nothing to do here
        return None

    def _finalize_file(self, cfg):
        # hook for new(): runs after seeding, before the final commit
        return None

    def _prepare_records(self, df):
        # hook for insert_records(): resolve or check input columns; none here
        return df

    def execute_sql(self, sql):
        """
        Execute SQL from a string or a ``.sql`` file path.

        :param sql: SQL text or path to a file with ``.sql`` extension
        :type sql: str or Path
        :return: None
        :rtype: None
        :raises FileNotFoundError: if ``sql`` has a ``.sql`` suffix but the file does not exist
        """
        sql_text = self._read_sql(sql=sql)
        self.conn.executescript(sql_text)
        return None

    def query_sql(self, sql, params=None):
        """
        Execute a SELECT query and return the result as a DataFrame.

        Accepts SQL text or a path to a ``.sql`` file.

        :param sql: SQL text or path to a file with ``.sql`` extension
        :type sql: str or Path
        :param params: positional parameters bound to ``?`` placeholders
        :type params: list or tuple, optional
        :return: query result; no datetime conversion is applied — epoch columns
            remain as integers unless the SQL itself handles the transformation
        :rtype: pandas.DataFrame
        :raises FileNotFoundError: if ``sql`` has a ``.sql`` suffix but the file does not exist

        Example — convert epoch to a readable UTC string directly in SQLite::

            df = db.query_sql(
                sql="SELECT datetime(datetime, 'unixepoch') AS dt, value FROM records LIMIT 10"
            )
        """
        sql_text = self._read_sql(sql=sql)
        return pd.read_sql(sql=sql_text, con=self.conn, params=params)

    @staticmethod
    def parse_setup(setup):
        """
        Parse a database setup configuration into a plain dict.

        Accepts a dict, a path to a TOML file, or a path to a JSON file.

        :param setup: configuration source
        :type setup: dict, str, or Path
        :return: configuration dict
        :rtype: dict
        :raises ValueError: if the file extension is not supported
        """
        if isinstance(setup, dict):
            return setup
        path = Path(setup)
        if path.suffix == ".toml":
            with open(path, "rb") as f:
                return tomllib.load(f)
        if path.suffix == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
        raise ValueError(f"Unsupported setup format: {path.suffix!r}")

    def new(self, config, overwrite=False):
        """
        Create a new database file from a setup configuration.

        Creation is all or nothing: on any error the partial file is removed.

        Expected configuration structure (TOML example)::

            [database]
            path = "path/to/hydro.db"

            [specs]
            path = "path/to/my_specs.csv"   # or .json — format detected by extension

            [catalogs]           # optional overrides; omitted keys fall back to defaults
            variables = "path/to/my_variables.csv"

        :param config: setup dict or path to a TOML/JSON file
        :type config: dict, str, or Path
        :param overwrite: delete and recreate the file if it already exists
        :type overwrite: bool
        :return: path to the created database file
        :rtype: Path
        :raises FileExistsError: if the database file already exists and ``overwrite`` is ``False``
        :raises FileNotFoundError: if the specs file or a table's SQL file does not exist
        :raises ValueError: if a spec has an invalid or duplicated name, unknown
            columns, unparseable dates, or points to unknown catalogue entries
        """
        cfg = self.parse_setup(setup=config)
        file_db = Path(cfg["database"]["path"])
        if file_db.exists():
            if not overwrite:
                raise FileExistsError(f"Database already exists: {file_db}")
            file_db.unlink()

        try:
            self._prepare_file(cfg=cfg, file_db=file_db)
            self.connect(file_db=file_db)

            # create all tables in dependency order; child SQL_DIR overrides base
            for table in self._TABLES:
                self._create_table(table=table)

            # seed catalogue tables; missing files are silently skipped
            catalogs = cfg.get("catalogs", {})
            self._seed_catalog(
                table="variables",
                file_path=catalogs.get("variables", self.variables_default),
            )
            self._seed_catalog(
                table="flags", file_path=catalogs.get("flags", self.flags_default)
            )
            self._seed_catalog(
                table="statistics",
                file_path=catalogs.get("statistics", self.statistics_default),
            )
            self._seed_catalog(
                table="sources", file_path=catalogs.get("sources", self.sources_default)
            )

            # seed specs (required; abort if file is missing)
            specs_file = Path(cfg["specs"]["path"])
            if not specs_file.is_file():
                raise FileNotFoundError(f"Specs file not found: {specs_file}")
            self._seed_catalog(table="specs", file_path=specs_file)

            self._finalize_file(cfg=cfg)
            self.conn.commit()

        except Exception:
            # creation must be error-free; roll back and remove the partial file
            self.close()
            if file_db.exists():
                file_db.unlink()
            raise

        return file_db

    @staticmethod
    def _to_epoch(series):
        # convert a text/datetime series to integer epoch seconds; null values stay null
        if pd.api.types.is_integer_dtype(series):
            return series
        converted = pd.to_datetime(arg=series, utc=True, errors="coerce")
        # non-null inputs that failed to parse
        bad = series[converted.isna() & series.notna()]
        if len(bad):
            raise ValueError(
                f"{len(bad)} unparseable date(s) in {series.name!r}, "
                f"eg: {bad.head(3).tolist()}"
            )
        # whole seconds since epoch; nullable so missing values stay NULL
        epoch = (converted - pd.Timestamp(0, tz="UTC")) // pd.Timedelta(seconds=1)
        return epoch.astype("Int64")

    @staticmethod
    def _apply_columns_map(df, columns_map):
        # resolve {db_col: csv_name_or_index} to a pandas rename dict and apply it
        rename = {}
        for db_col, src in columns_map.items():
            if isinstance(src, int):
                rename[df.columns[src]] = db_col
            else:
                rename[src] = db_col
        return df.rename(columns=rename)

    def _seed_catalog(self, table, file_path):
        # insert rows from a CSV or JSON file into a table; skips silently if absent
        path = Path(file_path)
        if not path.is_file():
            return
        if path.suffix == ".json":
            df = pd.read_json(path_or_buf=path)
        else:
            df = pd.read_csv(filepath_or_buffer=path, sep=self.file_csv_sep)
        for col in _EPOCH_COLS.get(table, ()):
            if col in df.columns:
                df[col] = self._to_epoch(series=df[col])
        self.insert_rows(dataframe=df, on_table=table)

    # SPEC NAMES
    # -------------------------------------------------------------------
    @staticmethod
    def _as_list(x):
        # scalars (numpy included) become one-item lists; iterables become lists
        if isinstance(x, str) or not hasattr(x, "__iter__"):
            return [x]
        return list(x)

    @staticmethod
    def _normalize_spec_name(name):
        # strip and uppercase, then validate the spec name format
        if not isinstance(name, str):
            raise ValueError(f"Spec name must be a string, got {name!r}")
        clean = name.strip().upper()
        if any(c.isspace() for c in clean):
            raise ValueError(
                f"Spec name {name!r} has whitespace inside; use underscores instead"
            )
        if not _SPEC_NAME_PATTERN.fullmatch(clean):
            raise ValueError(
                f"Invalid spec name {name!r}: use uppercase ASCII letters, digits "
                f"and underscores, starting with a letter (eg, PPT_MONTHLY_CHIRPS)"
            )
        return clean

    def _spec_lookup(self):
        # map spec names to ids
        return dict(self.conn.execute("SELECT name, id FROM specs").fetchall())

    def _check_specs(self, df):
        # normalize spec names; reject duplicates and unknown catalogue entries
        df["name"] = df["name"].apply(lambda x: self._normalize_spec_name(name=x))
        in_batch = set(df["name"][df["name"].duplicated()])
        in_table = set(df["name"]) & set(self._spec_lookup())
        dups = sorted(in_batch | in_table)
        if dups:
            raise ValueError(f"Duplicate spec name(s): {dups}")
        refs = {
            "variable_name": "variables",
            "statistic_name": "statistics",
            "source_name": "sources",
        }
        for col, table in refs.items():
            if col not in df.columns:
                continue
            valid = {r[0] for r in self.conn.execute(f"SELECT name FROM {table}")}
            bad = df.loc[~df[col].isin(valid), ["name", col]]
            if len(bad):
                pairs = [f"{n}: {v!r}" for n, v in bad.itertuples(index=False)]
                raise ValueError(f"Unknown {col} (not in {table}) for spec(s): {pairs}")
        return df

    def _resolve_spec_ids(self, spec_name=None, spec_id=None, required=True):
        """
        Resolve spec names or ids to a list of spec ids.

        ``spec_name`` always wins: if ``spec_id`` is also given and points to other
        specs, a warning is issued and ``spec_id`` is ignored.

        :param spec_name: one or more spec names; case and surrounding whitespace are ignored
        :type spec_name: str or list[str], optional
        :param spec_id: one or more spec ids, used only if ``spec_name`` is ``None``
        :type spec_id: int or list[int], optional
        :param required: raise if both are ``None``; otherwise return ``None``
        :type required: bool
        :return: spec ids, or ``None`` if nothing was given and not required
        :rtype: list[int] or None
        :raises ValueError: if a name or id is unknown, or both are ``None`` while required
        """
        if spec_name is None and spec_id is None:
            if required:
                raise ValueError("Provide spec_name (preferred) or spec_id")
            return None
        lookup = self._spec_lookup()
        # operator.index accepts python and numpy integers only
        ids_given = (
            None
            if spec_id is None
            else [operator.index(i) for i in self._as_list(spec_id)]
        )
        if spec_name is not None:
            names = [
                self._normalize_spec_name(name=n) for n in self._as_list(spec_name)
            ]
            unknown = [n for n in names if n not in lookup]
            if unknown:
                raise ValueError(
                    f"Unknown spec_name(s): {unknown}. Valid: {sorted(lookup)}"
                )
            ids = [lookup[n] for n in names]
            if ids_given is not None and set(ids_given) != set(ids):
                warnings.warn(
                    f"spec_name {names} and spec_id {ids_given} point to different "
                    f"specs; spec_name was used",
                    stacklevel=3,
                )
            return ids
        valid = {sid: name for name, sid in lookup.items()}
        unknown = [i for i in ids_given if i not in valid]
        if unknown:
            raise ValueError(f"Unknown spec_id(s): {unknown}. Valid: {valid}")
        return ids_given

    # FLAGS AND DOMAINS
    # -------------------------------------------------------------------
    def _flag_value(self, name, required=True):
        # flag value by flag name; None if absent and not required
        row = self.conn.execute(
            "SELECT value FROM flags WHERE name = ?", (name,)
        ).fetchone()
        if row is None and required:
            raise ValueError(f"Flag {name!r} not found in the flags table")
        return None if row is None else row[0]

    @staticmethod
    def _parse_domain(domain):
        """
        Parse a domain string into a list of intervals.

        See the module notes for the notation. Single points are allowed
        (``[5U5]``); empty intervals raise.

        :param domain: domain notation, eg ``[0U)`` or ``[-90U-60]U[60U90]``
        :type domain: str
        :return: intervals as ``(lower, upper, lower_closed, upper_closed)``;
            unbounded sides are ``-inf`` and ``inf``
        :rtype: list[tuple[float, float, bool, bool]]
        :raises ValueError: if the notation is invalid or an interval is empty
        """
        if not isinstance(domain, str) or not _DOMAIN_PATTERN.fullmatch(domain):
            raise ValueError(
                f"Invalid domain {domain!r}: use intervals like [0U), (0U1] or (U), "
                f"joined by U"
            )
        intervals = []
        for left, low, high, right in _INTERVAL_PATTERN.findall(domain):
            try:
                lower = float(low) if low else -np.inf
                upper = float(high) if high else np.inf
            except ValueError:
                raise ValueError(f"Invalid bound in domain {domain!r}") from None
            lower_closed = left == "["
            upper_closed = right == "]"
            if lower > upper or (
                lower == upper and not (lower_closed and upper_closed)
            ):
                raise ValueError(f"Empty interval in domain {domain!r}")
            intervals.append((lower, upper, lower_closed, upper_closed))
        return intervals

    @staticmethod
    def _in_domain(values, domain):
        # boolean array: True where values fall in any interval of the domain
        v = np.asarray(values, dtype=float)
        inside = np.zeros(v.shape, dtype=bool)
        for lower, upper, lower_closed, upper_closed in DataBase._parse_domain(
            domain=domain
        ):
            above = v >= lower if lower_closed else v > lower
            below = v <= upper if upper_closed else v < upper
            inside |= above & below
        return inside

    def _check_variables(self, df):
        # reject variables whose domain cannot be parsed
        for name, domain in zip(df["name"], df["domain"]):
            try:
                self._parse_domain(domain=domain)
            except ValueError as e:
                raise ValueError(f"Variable {name!r}: {e}") from None
        return df

    def _flag_out_of_domain(self, df, spec_id):
        # turn regular rows with actual values outside the variable domain into suspect
        name, domain = self.conn.execute(
            "SELECT s.name, v.domain FROM specs s "
            "JOIN variables v ON s.variable_name = v.name WHERE s.id = ?",
            (spec_id,),
        ).fetchone()
        regular = self._flag_value(name="regular", required=False)
        suspect = self._flag_value(name="suspect", required=False)
        if regular is None or suspect is None:
            warnings.warn(
                "Flags 'regular' or 'suspect' not in this database; domain check skipped",
                stacklevel=3,
            )
            return df
        values = df["value"]
        out = (
            values.notna()
            & ~self._in_domain(values=values, domain=domain)
            & (df["flag_value"] == regular)
        )
        if out.any():
            df.loc[out, "flag_value"] = suspect
            warnings.warn(
                f"{int(out.sum())} value(s) of {name} outside {domain} flagged suspect",
                stacklevel=3,
            )
        return df

    # INSERTS
    # -------------------------------------------------------------------
    @contextmanager
    def transaction(self):
        """
        Group several inserts into one atomic block.

        The block commits on success and rolls back on any exception, which is
        re-raised. Blocks can be nested: a failed inner block rolls back only its
        own changes, and only the outermost block commits. Outside a block, each
        public insert commits on its own.

        Do not call :meth:`execute_sql` inside a block: ``executescript`` commits
        any pending transaction first.

        :return: this database
        :rtype: DataBase

        :Example:

        .. code-block:: python

            with db.transaction():
                for name, df in batches.items():
                    db.insert_records(dataframe=df, spec_name=name)
        """
        # savepoints nest; releasing the outermost one ends the transaction
        name = f"tx_{self._tx_depth}"
        self.conn.execute(f"SAVEPOINT {name}")
        self._tx_depth += 1
        try:
            yield self
        except BaseException:
            self.conn.execute(f"ROLLBACK TO {name}")
            self.conn.execute(f"RELEASE {name}")
            raise
        else:
            self.conn.execute(f"RELEASE {name}")
        finally:
            self._tx_depth -= 1
        # commit a transaction opened before the block (eg, by raw sql)
        if self._tx_depth == 0 and self.conn.in_transaction:
            self.conn.commit()

    def insert_rows(self, dataframe, on_table, columns_map=None, drop_extra=False):
        """
        Insert DataFrame rows into a table.

        Columns the target table does not have raise an error, unless
        ``drop_extra`` is ``True``. Rows for ``specs`` get their ``name``
        normalized and checked for duplicates and unknown catalogue entries.

        The insert is atomic: a failure leaves no rows. It commits at the end,
        unless it runs inside :meth:`transaction`.

        :param dataframe: source data
        :type dataframe: pandas.DataFrame
        :param on_table: target table name
        :type on_table: str
        :param columns_map: column mapping ``{db_col: csv_name_or_index}``; values may be
            a string (source column name) or an int (source column position, 0-based)
        :type columns_map: dict, optional
        :param drop_extra: drop columns the target table does not have instead of raising
        :type drop_extra: bool
        :return: None
        :rtype: None
        :raises ValueError: if there are extra columns and ``drop_extra`` is ``False``,
            or if a spec is invalid, duplicated or points to unknown catalogue entries
        """
        df = dataframe.copy()
        if columns_map:
            df = self._apply_columns_map(df=df, columns_map=columns_map)
        cursor = self.conn.execute(f"PRAGMA table_info({on_table})")
        table_cols = {row[1] for row in cursor.fetchall()}
        extra = [c for c in df.columns if c not in table_cols]
        if extra and not drop_extra:
            raise ValueError(f"Columns not in table {on_table!r}: {extra}")
        df = df.drop(columns=extra)
        if on_table == "specs" and "name" in df.columns:
            df = self._check_specs(df=df)
        if on_table == "variables" and "domain" in df.columns:
            df = self._check_variables(df=df)

        # python scalars for binding; missing values become NULL
        values = df.astype(object).where(df.notna(), None)
        cols = ", ".join(f'"{c}"' for c in df.columns)
        marks = ", ".join("?" * len(df.columns))
        sql = f'INSERT INTO "{on_table}" ({cols}) VALUES ({marks})'
        with self.transaction():
            for i in range(0, len(values), _CHUNK_SIZE):
                chunk = values.iloc[i : i + _CHUNK_SIZE]
                self.conn.executemany(sql, chunk.itertuples(index=False, name=None))
        return None

    def insert_row(self, row_dict, on_table, columns_map=None, drop_extra=False):
        """
        Insert a single row from a plain dict into any table.

        Convenience wrapper around :meth:`insert_rows` for one-row inserts.
        Epoch conversion is applied automatically for date columns in tables
        listed in ``_EPOCH_COLS`` (e.g. ``start`` and ``end`` in ``specs``).

        :param row_dict: row fields as a dict
        :type row_dict: dict
        :param on_table: target table name
        :type on_table: str
        :param columns_map: column mapping ``{db_col: csv_name_or_index}``
        :type columns_map: dict, optional
        :return: None
        :rtype: None
        """
        df = pd.DataFrame([row_dict])
        for col in _EPOCH_COLS.get(on_table, ()):
            if col in df.columns:
                df[col] = self._to_epoch(series=df[col])
        self.insert_rows(
            dataframe=df,
            on_table=on_table,
            columns_map=columns_map,
            drop_extra=drop_extra,
        )
        return None

    def insert_records(
        self,
        dataframe,
        spec_id=None,
        spec_name=None,
        flag=None,
        columns_map=None,
        transform_values=True,
        nan_policy="drop",
        drop_extra=False,
        check_domain=True,
    ):
        """
        Insert records into the ``records`` table for a given spec.

        The spec is given by ``spec_name`` (preferred) or ``spec_id`` and is
        broadcast to all rows in the batch. If both are given and disagree,
        ``spec_name`` is used and a warning is issued. The ``datetime``
        column is converted from text to epoch seconds automatically. The
        optional linear transform (``stored = actual * scale + offset``) is
        resolved from the matching row in ``specs``.

        NaN in ``value`` follows ``nan_policy``: ``"drop"`` skips those rows;
        ``"void"`` stores them as NULL with the ``void`` flag, overriding the
        batch flag, so a known gap can be told apart from data never loaded.
        Rows whose flag is already a no-value flag (0 or below, eg
        ``notanalysed``) are kept as given under both policies.

        With ``check_domain``, actual values outside the variable domain
        (see the module notes on domain notation) turn ``regular`` rows into
        ``suspect`` and issue a warning. Values are kept; other flags are left as given.

        Inputs are validated before anything is written: unknown flags,
        unparseable dates and columns ``records`` does not have raise an error.

        .. warning::

            Spec ids depend on the order specs were created, so the same id can
            point to different datasets in two database files. Prefer ``spec_name``.

        :param dataframe: source data; must contain the columns in :attr:`_RECORD_COLUMNS`
            (``datetime`` and ``value`` in the base class); ``flag_value`` is also
            required unless ``flag`` is provided
        :type dataframe: pandas.DataFrame
        :param spec_id: id of the spec; used only if ``spec_name`` is ``None``
        :type spec_id: int, optional
        :param spec_name: name of the spec (preferred); case is ignored
        :type spec_name: str, optional
        :param flag: if given, overwrite or create the ``flag_value`` column with this constant
        :type flag: int, optional
        :param columns_map: column mapping ``{db_col: csv_name_or_index}``; values may be
            a string (source column name) or an int (source column position, 0-based)
        :type columns_map: dict, optional
        :param transform_values: apply linear transform if True
        :type transform_values: bool
        :param nan_policy: for NaN values with a positive flag, ``"drop"`` skips them and ``"void"`` stores them as void records
        :type nan_policy: str
        :param drop_extra: drop columns ``records`` does not have instead of raising
        :type drop_extra: bool
        :param check_domain: flag values outside the variable domain as ``suspect``
        :type check_domain: bool
        :return: None
        :rtype: None
        :raises ValueError: if no spec is given, the spec is unknown, more than one spec
            is given, a required column is missing, ``nan_policy`` is unknown, or a
            flag, date or column is invalid
        """
        if nan_policy not in ("drop", "void"):
            raise ValueError(f"nan_policy must be 'drop' or 'void', got {nan_policy!r}")
        ids = self._resolve_spec_ids(spec_name=spec_name, spec_id=spec_id)
        if len(ids) != 1:
            raise ValueError(f"Records are inserted for a single spec, got {len(ids)}")
        spec_id = ids[0]
        df = dataframe.copy()
        if columns_map:
            df = self._apply_columns_map(df=df, columns_map=columns_map)
        df = self._prepare_records(df=df)
        required = set(self._RECORD_COLUMNS)
        if flag is None:
            required.add("flag_value")
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
        df["spec_id"] = spec_id
        if flag is not None:
            df["flag_value"] = flag
        df["datetime"] = self._to_epoch(series=df["datetime"])

        # NaN values with a positive flag: drop, or keep as void (NULL value,
        # void flag); rows already flagged as no-value (<= 0) are kept as given
        nan = df["value"].isna() & (df["flag_value"] > 0)
        if nan_policy == "drop":
            df = df[~nan].copy()
        elif nan.any():
            df.loc[nan, "flag_value"] = self._flag_value(name="void")

        # domain check on actual values: regular rows outside become suspect
        if check_domain:
            df = self._flag_out_of_domain(df=df, spec_id=spec_id)

        valid = {r[0] for r in self.conn.execute("SELECT value FROM flags")}
        unknown = set(df["flag_value"].unique()) - valid
        if unknown:
            unknown = [v.item() if hasattr(v, "item") else v for v in unknown]
            raise ValueError(
                f"Unknown flag_value(s): {unknown}. Valid: {sorted(valid)}"
            )
        if transform_values and "value" in df.columns:
            row = self.conn.execute(
                "SELECT scale, offset FROM specs WHERE id = ?", (spec_id,)
            ).fetchone()
            if row:
                scale, offset = row
                df["value"] = df["value"] * scale + offset
        self.insert_rows(dataframe=df, on_table="records", drop_extra=drop_extra)
        return None

    def insert_record(
        self,
        row_dict,
        spec_id=None,
        spec_name=None,
        flag=None,
        columns_map=None,
        transform_values=True,
        nan_policy="drop",
        drop_extra=False,
        check_domain=True,
    ):
        """
        Insert a single record from a plain dict.

        Convenience wrapper around :meth:`insert_records` for one-row inserts.

        .. warning::

            Spec ids depend on the order specs were created, so the same id can
            point to different datasets in two database files. Prefer ``spec_name``.

        :param row_dict: record fields, e.g. ``{"datetime": "2024-01-01", "value": 12.3}``
        :type row_dict: dict
        :param spec_id: id of the spec; used only if ``spec_name`` is ``None``
        :type spec_id: int, optional
        :param spec_name: name of the spec (preferred); case is ignored
        :type spec_name: str, optional
        :param flag: if given, overwrite or create the ``flag_value`` column with this constant
        :type flag: int, optional
        :param columns_map: column mapping ``{db_col: csv_name_or_index}``; values may be
            a string (source column name) or an int (source column position, 0-based)
        :type columns_map: dict, optional
        :param transform_values: apply linear transform if True
        :type transform_values: bool
        :param nan_policy: for NaN values with a positive flag, ``"drop"`` skips them and ``"void"`` stores them as void records
        :type nan_policy: str
        :param drop_extra: drop columns ``records`` does not have instead of raising
        :type drop_extra: bool
        :param check_domain: flag values outside the variable domain as ``suspect``
        :type check_domain: bool
        :return: None
        :rtype: None
        """
        self.insert_records(
            dataframe=pd.DataFrame([row_dict]),
            spec_id=spec_id,
            spec_name=spec_name,
            flag=flag,
            columns_map=columns_map,
            transform_values=transform_values,
            nan_policy=nan_policy,
            drop_extra=drop_extra,
            check_domain=check_domain,
        )
        return None

    def load_records(
        self,
        files,
        spec_id=None,
        spec_name=None,
        sep=None,
        flag=None,
        columns_map=None,
        transform_values=True,
        nan_policy="drop",
        drop_extra=False,
        check_domain=True,
    ):
        """
        Load records from a list of CSV files into the ``records`` table.

        All files are read and concatenated, then inserted via
        :meth:`insert_records`. See that method for column requirements and
        transform behaviour.

        .. warning::

            Spec ids depend on the order specs were created, so the same id can
            point to different datasets in two database files. Prefer ``spec_name``.

        :param files: paths to CSV files to load
        :type files: list[str or Path]
        :param spec_id: id of the spec; used only if ``spec_name`` is ``None``
        :type spec_id: int, optional
        :param spec_name: name of the spec (preferred); case is ignored
        :type spec_name: str, optional
        :param sep: column separator; ``None`` uses :attr:`file_csv_sep`
        :type sep: str, optional
        :param flag: if given, overwrite or create the ``flag_value`` column with this constant
        :type flag: int, optional
        :param columns_map: column mapping ``{db_col: csv_name_or_index}``; values may be
            a string (source column name) or an int (source column position, 0-based)
        :type columns_map: dict, optional
        :param transform_values: apply linear transform if True
        :type transform_values: bool
        :param nan_policy: for NaN values with a positive flag, ``"drop"`` skips them and ``"void"`` stores them as void records
        :type nan_policy: str
        :param drop_extra: drop columns ``records`` does not have instead of raising
        :type drop_extra: bool
        :param check_domain: flag values outside the variable domain as ``suspect``
        :type check_domain: bool
        :return: None
        :rtype: None
        """
        _sep = sep if sep is not None else self.file_csv_sep
        frames = [pd.read_csv(filepath_or_buffer=Path(f), sep=_sep) for f in files]
        df_all = pd.concat(objs=frames, ignore_index=True)
        self.insert_records(
            dataframe=df_all,
            spec_id=spec_id,
            spec_name=spec_name,
            flag=flag,
            columns_map=columns_map,
            transform_values=transform_values,
            nan_policy=nan_policy,
            drop_extra=drop_extra,
            check_domain=check_domain,
        )
        return None

    def query_records(self, query_dict=None, quiet=True):
        """
        Query the ``records`` table with optional filters combined with AND logic.

        Filters and options are passed as a single dict so the interface stays
        stable as new keys are added. All keys are optional; an empty or absent
        dict returns the full table. Unknown keys raise an error.

        Filter keys:

        - ``spec_name`` (*str* or *list[str]*) — one or more spec names (preferred);
          case is ignored; wins over ``spec_id`` with a warning if both disagree
        - ``spec_id`` (*int* or *list[int]*) — one or more spec ids, used only without ``spec_name``
        - ``start`` (*str*) — lower datetime bound (inclusive); any format parseable by pandas
        - ``end`` (*str*) — upper datetime bound (inclusive)
        - ``flag_value`` (*int* or *list[int]*) — one or more flag values to include

        Option keys:

        - ``transform_values`` (*bool*, default ``True``) — reverse the linear transform
          so ``value`` holds actual values via ``actual = (stored - offset) / scale``
        - ``wide`` (*bool*, default ``False``) — one column per spec, indexed by ``datetime``
        - ``aggfunc`` (*str* or *callable*, default ``None``) — with ``wide``, aggregate
          replicates at the same datetime (eg, ``"mean"``); ``None`` raises on replicates
        - ``with_meta`` (*bool*, default ``False``) — add variable, units, statistic and
          source; as columns in long format, as ``df.attrs["specs"]`` in wide format

        The long format is ordered by spec, then datetime, and carries both
        ``spec_name`` and ``spec_id``. Without ``spec_name`` and ``spec_id``,
        records of all specs are returned. ``datetime`` is always a
        timezone-aware (UTC) pandas datetime.

        .. warning::

            Spec ids depend on the order specs were created, so the same id can
            point to different datasets in two database files. Prefer ``spec_name``.

        :param query_dict: filter and option keys (see above)
        :type query_dict: dict, optional
        :param quiet: if ``False``, prints elapsed query time to stdout
        :type quiet: bool
        :return: matching records, in long or wide format
        :rtype: pandas.DataFrame
        :raises ValueError: if a key is unknown, ``aggfunc`` is given without ``wide``,
            or ``wide`` meets replicates without ``aggfunc``

        :Example:

        .. code-block:: python

            df = db.query_records(
                query_dict={
                    "spec_name": ["PPT_MONTHLY_CHIRPS", "Q_MONTHLY_ANA"],
                    "start": "2000-01-01",
                    "wide": True,
                    "with_meta": True,
                }
            )
            meta = df.attrs["specs"]
        """
        q = query_dict or {}
        unknown = sorted(set(q) - set(self._QUERY_KEYS))
        if unknown:
            raise ValueError(
                f"Unknown query key(s): {unknown}. Valid: {list(self._QUERY_KEYS)}"
            )
        transform_values = q.get("transform_values", True)
        wide = q.get("wide", False)
        aggfunc = q.get("aggfunc")
        with_meta = q.get("with_meta", False)
        if aggfunc is not None and not wide:
            raise ValueError("aggfunc requires wide=True")

        conditions, params = self._query_filters(query_dict=q)
        sql = self._query_source()
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        # result columns; r.id keeps replicates in insertion order
        sql += " ORDER BY " + ", ".join(self._ORDER_BY) + ", r.id"

        t0 = time.perf_counter()
        df = pd.read_sql(sql=sql, con=self.conn, params=params)
        elapsed = time.perf_counter() - t0

        # output
        # -------------------------------------------------------------------
        for col in self._EPOCH_OUTPUT:
            df[col] = pd.to_datetime(df[col], unit="s", utc=True)
        if transform_values:
            df["value"] = (df["value"] - df["offset"]) / df["scale"]
        df = df.drop(columns=["scale", "offset"])

        meta = self._spec_meta(names=df["spec_name"].unique()) if with_meta else None
        if wide:
            df = self._to_wide(df=df, aggfunc=aggfunc)
            if with_meta:
                df.attrs["specs"] = meta
        elif with_meta:
            df = df.merge(meta, on="spec_name", how="left")

        if not quiet:
            print(f"[query_records] {len(df)} rows in {elapsed:.3f}s")
        return df

    def _query_source(self):
        # SELECT and FROM of query_records; records are aliased r, specs s
        return (
            "SELECT r.*, s.name AS spec_name, s.scale, s.offset "
            "FROM records r JOIN specs s ON r.spec_id = s.id"
        )

    def _query_filters(self, query_dict):
        """
        Build the WHERE conditions of :meth:`query_records`.

        Child classes extend this to add their own filter keys.

        :param query_dict: validated query keys
        :type query_dict: dict
        :return: SQL conditions (combined with AND) and their bound parameters
        :rtype: tuple[list[str], list]
        """
        q = query_dict
        conditions = []
        params = []

        if q.get("start") is not None:
            conditions.append(f"{self._TIME_SQL} >= ?")
            params.append(int(pd.Timestamp(q["start"], tz="UTC").timestamp()))

        if q.get("end") is not None:
            conditions.append(f"{self._TIME_SQL} <= ?")
            params.append(int(pd.Timestamp(q["end"], tz="UTC").timestamp()))

        if q.get("flag_value") is not None:
            vals = [operator.index(v) for v in self._as_list(q["flag_value"])]
            conditions.append(f"r.flag_value IN ({','.join('?' * len(vals))})")
            params.extend(vals)

        spec_ids = self._resolve_spec_ids(
            spec_name=q.get("spec_name"), spec_id=q.get("spec_id"), required=False
        )
        if spec_ids is not None:
            conditions.append(f"r.spec_id IN ({','.join('?' * len(spec_ids))})")
            params.extend(spec_ids)

        return conditions, params

    def _spec_meta(self, names):
        # one row per spec name, in the given order: variable, units, statistic, source
        sql = (
            "SELECT s.name AS spec_name, s.variable_name, v.units, "
            "s.statistic_name, s.source_name "
            "FROM specs s JOIN variables v ON s.variable_name = v.name"
        )
        meta = pd.read_sql(sql=sql, con=self.conn).set_index("spec_name")
        return meta.loc[list(names)].reset_index()

    def _to_wide(self, df, aggfunc=None):
        """
        Pivot long records to a wide table indexed by :attr:`_WIDE_INDEX` (``datetime`` here).

        Columns are keyed by :attr:`_WIDE_COLUMNS`, in order of appearance.
        Replicates on the same keys and datetime raise unless ``aggfunc`` is given.

        :param df: long-format records from :meth:`query_records`
        :type df: pandas.DataFrame
        :param aggfunc: pandas aggregation name (eg, ``"mean"``) or callable
        :type aggfunc: str or callable, optional
        :return: wide table, one column per key combination
        :rtype: pandas.DataFrame
        :raises ValueError: if there are replicates and ``aggfunc`` is ``None``
        """
        keys = list(self._WIDE_COLUMNS)
        columns = keys[0] if len(keys) == 1 else keys
        if aggfunc is None:
            dups = df[df.duplicated(subset=keys + [self._WIDE_INDEX], keep=False)]
            if len(dups):
                counts = dups.groupby(keys + [self._WIDE_INDEX]).size()
                examples = [
                    f"{' / '.join(map(str, k[:-1]))} at {k[-1]} has {n} values"
                    for k, n in counts.head(3).items()
                ]
                raise ValueError(
                    f"{len(counts)} replicated entries, eg: {examples}; "
                    f"pass aggfunc to aggregate"
                )
            wide = df.pivot(index=self._WIDE_INDEX, columns=columns, values="value")
        else:
            wide = df.pivot_table(
                index=self._WIDE_INDEX,
                columns=columns,
                values="value",
                aggfunc=aggfunc,
            )
        # keep the query order (spec, then extra keys) instead of sorted columns
        order = df[keys].drop_duplicates()
        if len(keys) == 1:
            order = pd.Index(order[keys[0]], name=keys[0])
        else:
            order = pd.MultiIndex.from_frame(order)
        return wide.reindex(columns=order)


class SemiSpatialDB(DataBase):
    """
    Database whose records carry a ``feature_id``.

    Features are not stored in the database: ``feature_id`` is an integer
    key (eg, an H3 cell index or a grid cell id) that points to a layer kept
    elsewhere. Spatial selection happens outside, and the selected ids are
    passed to :meth:`query_records`.

    Only ``records`` differs from :class:`DataBase`; all other tables come
    from the base schema.

    Children rename the key by setting ``_FEATURE_KEY`` (eg, ``zone_id``);
    the record, query, ordering and wide-format hooks follow it.

    :param name: database name
    :type name: str
    :param alias: short alias
    :type alias: str, optional

    :Example:

    .. code-block:: python

        import geopandas as gpd

        cells = gpd.read_file("grid.gpkg", layer="cells")
        basin = gpd.read_file("basin.gpkg")
        ids = gpd.sjoin(cells, basin, predicate="intersects")["id"].tolist()

        df = db.query_records(
            query_dict={"spec_name": "PPT_MONTHLY_CHIRPS", "feature_id": ids}
        )
        basin_mean = df.groupby("datetime")["value"].mean()
    """

    # this is /src/plans/data/sql/semispatial
    SQL_DIR = DATA_SQL_DIR / "semispatial"

    _FEATURE_KEY = "feature_id"
    _RECORD_COLUMNS = DataBase._RECORD_COLUMNS + (_FEATURE_KEY,)
    _QUERY_KEYS = DataBase._QUERY_KEYS + (_FEATURE_KEY,)
    _ORDER_BY = ("spec_id", _FEATURE_KEY, "datetime")
    _WIDE_COLUMNS = ("spec_name", _FEATURE_KEY)

    def __init_subclass__(cls, **kwargs):
        """
        Swap the inherited feature key for the child's own in the column hooks.

        A child sets only ``_FEATURE_KEY``; the hooks it inherits are renamed,
        and so is the matching ``_name`` key (``feature_id`` to ``zone_id``
        also turns ``feature_name`` into ``zone_name``). Hooks written in the
        child's own body are used as written.
        """
        super().__init_subclass__(**kwargs)
        # nearest ancestor that defines the key is the one the hooks were built on
        parent_key = next(
            base._FEATURE_KEY
            for base in cls.__mro__[1:]
            if "_FEATURE_KEY" in vars(base)
        )
        key = cls._FEATURE_KEY
        swap = {
            parent_key: key,
            parent_key.removesuffix("_id") + "_name": key.removesuffix("_id") + "_name",
        }
        for hook in ("_RECORD_COLUMNS", "_QUERY_KEYS", "_ORDER_BY", "_WIDE_COLUMNS"):
            if hook in vars(cls):
                continue
            columns = getattr(cls, hook)
            setattr(cls, hook, tuple(swap.get(c, c) for c in columns))

    def _query_filters(self, query_dict):
        """
        Build the WHERE conditions of :meth:`query_records`, adding the feature key.

        The key (:attr:`_FEATURE_KEY`) takes an int or any iterable of ints
        (numpy included). The ids are bound as one JSON array, so their number
        is not limited by the SQLite cap on bound parameters.

        :param query_dict: validated query keys
        :type query_dict: dict
        :return: SQL conditions (combined with AND) and their bound parameters
        :rtype: tuple[list[str], list]
        """
        conditions, params = super()._query_filters(query_dict=query_dict)
        key = self._FEATURE_KEY
        feature_ids = query_dict.get(key)
        if feature_ids is not None:
            ids = [operator.index(i) for i in self._as_list(feature_ids)]
            conditions.append(f"r.{key} IN (SELECT value FROM json_each(?))")
            params.append(json.dumps(ids))
        return conditions, params


class SpatialDB(SemiSpatialDB):
    """
    GeoPackage database whose records point to features stored in the same file.

    The file holds one layer of features next to the standard tables. Each
    feature has an ``id``, a unique ``name``, a ``geometry`` and any extra
    columns of the source. Records carry ``feature_id``, a real foreign key to
    the layer, so a record cannot point to a missing feature.

    This class stores any geometry type, mixed in one ``features`` layer.
    Its children :class:`ZonesDB`, :class:`PathsDB` and :class:`SitesDB`
    accept one kind only and rename the layer and key after it (eg, ``zones``
    and ``zone_id``). A child sets the layer name, the record key and the
    accepted geometry types; the SQL templates in ``sql/spatial`` are filled
    from them.

    The layer is written and extended through geopandas only. Plain SQLite
    cannot insert into it, because the GeoPackage triggers call functions that
    only GDAL defines. All other tables work as in :class:`DataBase`.

    The setup file adds a ``[spatial]`` section with the source geometries::

        [database]
        path = "basins.gpkg"        # must be a .gpkg file

        [spatial]
        file = "my_basins.shp"      # any format geopandas reads
        layer = "basins"            # optional, for files with several layers

    The source needs a ``name`` column with unique values. An integer ``id``
    column, if present, is kept as the feature id.

    .. warning::

        Tables are STRICT, a feature of SQLite 3.37 (2021). Readers built on an
        older SQLite (eg, an old QGIS or GDAL) cannot open the file at all.

    :param name: database name
    :type name: str
    :param alias: short alias
    :type alias: str, optional
    """

    # this is /src/plans/data/sql/spatial (templates for records and layer)
    SQL_DIR = DATA_SQL_DIR / "spatial"

    # layer table, accepted geometry types (None: any), multi-part writing
    _LAYER = "features"
    _GEOMETRY_TYPES = None
    _PROMOTE_TO_MULTI = False
    # table that the record key points to; None means the layer
    _KEY_TABLE = None

    _QUERY_KEYS = SemiSpatialDB._QUERY_KEYS + ("feature_name",)

    def __init__(self, name, alias=None):
        super().__init__(name, alias)
        self.file_db = None  # path of the connected GeoPackage

    def connect(self, file_db):
        """
        Open a connection to a GeoPackage file.

        Keeps the file path, which geopandas needs to read and write the layer.

        :param file_db: path to the ``.gpkg`` file
        :type file_db: str or Path
        :return: active connection
        :rtype: sqlite3.Connection
        """
        self.file_db = Path(file_db)
        return super().connect(file_db=file_db)

    # FILE CREATION
    # -------------------------------------------------------------------
    def _fill_template(self, sql_text):
        # fill the {layer} and {key} placeholders of the spatial SQL templates
        return sql_text.replace("{layer}", self._LAYER).replace(
            "{key}", self._FEATURE_KEY
        )

    def _create_table(self, table):
        # run the table's .sql file with its placeholders filled
        sql_text = self._read_sql(sql=self._sql_path(table=table))
        self.conn.executescript(self._fill_template(sql_text=sql_text))

    def _prepare_file(self, cfg, file_db):
        # write the layer first: GeoPackage metadata tables exist only after it
        if Path(file_db).suffix != ".gpkg":
            raise ValueError(f"A spatial database must be a .gpkg file, got {file_db}")
        spatial = cfg.get("spatial", {})
        if "file" not in spatial:
            raise ValueError(
                "Missing [spatial] section with the source 'file' (and optional 'layer')"
            )
        gdf = gpd.read_file(filename=spatial["file"], layer=spatial.get("layer"))
        self._check_features(gdf=gdf)
        self._write_layer(gdf=gdf, file_db=file_db, mode="w")
        return None

    def _finalize_file(self, cfg):
        # unique layer names, then register the plain tables as GeoPackage attributes
        self._create_table(table="layer")
        self.conn.executemany(
            "INSERT INTO gpkg_contents (table_name, data_type, identifier) "
            "VALUES (?, 'attributes', ?)",
            [(table, table) for table in self._TABLES],
        )
        return None

    # FEATURES
    # -------------------------------------------------------------------
    def _check_features(self, gdf):
        # require unique text names and non-empty geometries of the accepted types
        if "name" not in gdf.columns:
            raise ValueError(f"The {self._LAYER} layer needs a 'name' column")
        names = gdf["name"]
        if names.isna().any() or not pd.api.types.is_string_dtype(names):
            raise ValueError(f"Every row of {self._LAYER} needs a text name")
        dups = sorted(set(names[names.duplicated()]))
        if dups:
            raise ValueError(f"Duplicate {self._LAYER} name(s): {dups}")
        empty = gdf.geometry.isna() | gdf.geometry.is_empty
        if empty.any():
            raise ValueError(
                f"{int(empty.sum())} row(s) without geometry, eg: "
                f"{names[empty].head(3).tolist()}"
            )
        if self._GEOMETRY_TYPES is None:
            return None
        bad = sorted(set(gdf.geom_type) - set(self._GEOMETRY_TYPES))
        if bad:
            raise ValueError(
                f"Geometry type(s) {bad} not accepted in {self._LAYER}. "
                f"Valid: {list(self._GEOMETRY_TYPES)}"
            )
        return None

    def _write_layer(self, gdf, file_db, mode):
        # GDAL keeps the GeoPackage triggers and the spatial index up to date;
        # a layer open to any type is declared generic, not typed by its first rows
        gdf.to_file(
            filename=file_db,
            layer=self._LAYER,
            driver="GPKG",
            mode=mode,
            geometry_type="Unknown" if self._GEOMETRY_TYPES is None else None,
            promote_to_multi=self._PROMOTE_TO_MULTI,
            FID="id",
            GEOMETRY_NAME="geometry",
        )
        return None

    def _name_lookup(self, table):
        # map names to ids in a table with name and id columns
        return dict(self.conn.execute(f"SELECT name, id FROM {table}").fetchall())

    def _resolve_names(self, names, table):
        # names to ids in a table; unknown names raise
        lookup = self._name_lookup(table=table)
        names = self._as_list(names)
        unknown = sorted(set(names) - set(lookup))
        if unknown:
            raise ValueError(f"Unknown {table} name(s): {unknown}")
        return [lookup[n] for n in names]

    @property
    def _key_table(self):
        # the table records point to: _KEY_TABLE, or the layer
        return self._KEY_TABLE or self._LAYER

    def insert_features(self, gdf):
        """
        Append features to the layer.

        Names must be new to the layer. Geometries are reprojected to the layer
        CRS. The write goes through geopandas on its own connection, so it cannot
        run inside a :meth:`transaction` block.

        :param gdf: features with a ``name`` column and optional extra columns
        :type gdf: geopandas.GeoDataFrame
        :return: None
        :rtype: None
        :raises ValueError: if names are missing, repeated or taken, geometry types
            are not accepted, or ``gdf`` has no CRS while the layer has one
        :raises RuntimeError: if called inside an open transaction
        """
        if self._tx_depth or self.conn.in_transaction:
            raise RuntimeError(
                "insert_features cannot run inside an open transaction; "
                "GDAL writes through its own connection"
            )
        self._check_features(gdf=gdf)
        taken = sorted(set(gdf["name"]) & set(self._name_lookup(table=self._LAYER)))
        if taken:
            raise ValueError(f"{self._LAYER} name(s) already in the database: {taken}")
        crs = gpd.read_file(filename=self.file_db, layer=self._LAYER, rows=0).crs
        if crs is not None:
            if gdf.crs is None:
                raise ValueError(
                    f"Geometries have no CRS; the layer uses {crs.to_string()}"
                )
            gdf = gdf.to_crs(crs=crs)
        self._write_layer(gdf=gdf, file_db=self.file_db, mode="a")
        return None

    def get_features(self, names=None):
        """
        Read the layer as a GeoDataFrame.

        :param names: one or more layer names; ``None`` returns the whole layer
        :type names: str or list[str], optional
        :return: layer rows with ``id`` as the first column (the record key values)
        :rtype: geopandas.GeoDataFrame
        :raises ValueError: if a name is unknown
        """
        gdf = gpd.read_file(filename=self.file_db, layer=self._LAYER, fid_as_index=True)
        gdf = gdf.rename_axis(index="id").reset_index()
        if names is not None:
            names = self._as_list(names)
            unknown = sorted(set(names) - set(gdf["name"]))
            if unknown:
                raise ValueError(f"Unknown {self._LAYER} name(s): {unknown}")
            gdf = gdf[gdf["name"].isin(names)].reset_index(drop=True)
        return gdf

    # RECORDS
    # -------------------------------------------------------------------
    def _prepare_records(self, df):
        # a name column (eg, zone_name) stands in for the key; unknown keys
        # are named clearly, though the foreign key would refuse them anyway
        key = self._FEATURE_KEY
        name_col = key.removesuffix("_id") + "_name"
        lookup = self._name_lookup(table=self._key_table)
        if key not in df.columns and name_col in df.columns:
            unknown = sorted(set(df[name_col].dropna()) - set(lookup))
            if unknown:
                raise ValueError(f"Unknown {self._key_table} name(s): {unknown[:5]}")
            df[key] = df[name_col].map(lookup)
            df = df.drop(columns=name_col)
        if key in df.columns:
            unknown = sorted(set(df[key].dropna().tolist()) - set(lookup.values()))
            if unknown:
                raise ValueError(
                    f"{len(unknown)} {key} value(s) not in {self._key_table}, "
                    f"eg: {unknown[:5]}"
                )
        return df

    def _query_filters(self, query_dict):
        """
        Build the WHERE conditions of :meth:`query_records`, adding the name key.

        The name key (eg, ``zone_name``) takes one or more names, resolved to
        ids through the table the records point to; unknown names raise.

        :param query_dict: validated query keys
        :type query_dict: dict
        :return: SQL conditions (combined with AND) and their bound parameters
        :rtype: tuple[list[str], list]
        """
        conditions, params = super()._query_filters(query_dict=query_dict)
        key = self._FEATURE_KEY
        names = query_dict.get(key.removesuffix("_id") + "_name")
        if names is not None:
            ids = self._resolve_names(names=names, table=self._key_table)
            conditions.append(f"r.{key} IN (SELECT value FROM json_each(?))")
            params.append(json.dumps(ids))
        return conditions, params


class ZonesDB(SpatialDB):
    """
    Spatial database of polygons (eg, basins or municipalities), in the ``zones`` layer.

    Records carry ``zone_id``, and queries also accept ``zone_name``.
    Polygons are written as multi-polygons, so single and multi-part zones
    share one layer.

    :param name: database name
    :type name: str
    :param alias: short alias
    :type alias: str, optional
    """

    _LAYER = "zones"
    _FEATURE_KEY = "zone_id"
    _GEOMETRY_TYPES = ("Polygon", "MultiPolygon")
    _PROMOTE_TO_MULTI = True


class PathsDB(SpatialDB):
    """
    Spatial database of lines (eg, rivers or transects), in the ``paths`` layer.

    Records carry ``path_id``, and queries also accept ``path_name``.
    Lines are written as multi-lines, so single and multi-part paths share
    one layer.

    :param name: database name
    :type name: str
    :param alias: short alias
    :type alias: str, optional
    """

    _LAYER = "paths"
    _FEATURE_KEY = "path_id"
    _GEOMETRY_TYPES = ("LineString", "MultiLineString")
    _PROMOTE_TO_MULTI = True


class SitesDB(SpatialDB):
    """
    Spatial database of points (eg, stations or wells), in the ``sites`` layer.

    Records carry ``site_id``, and queries also accept ``site_name``.

    :param name: database name
    :type name: str
    :param alias: short alias
    :type alias: str, optional
    """

    _LAYER = "sites"
    _FEATURE_KEY = "site_id"
    _GEOMETRY_TYPES = ("Point",)


class FieldDB(SitesDB):
    """
    Sites database for in situ measurements (eg, a climate station network).

    The instrument measures at the site, so records point straight to it by
    ``site_id``. It behaves as :class:`SitesDB` for now; the name marks the
    branch for features specific to field data.

    :param name: database name
    :type name: str
    :param alias: short alias
    :type alias: str, optional
    """


class LabDB(SitesDB):
    """
    Sites database for laboratory analyses of field samples.

    Data follows the chain ``sites -> samples -> mixtures -> records``.
    A sample (eg, a water bottle) is taken at a site at a sampling time. The
    lab analyses a mixture of one or more samples; most mixtures hold a single
    sample, and a sample may enter several mixtures. Records carry
    ``mixture_id`` and the analysis time, which may be unknown (NULL). There is
    no aliquot table: the mixture stands for whatever the lab analysed.

    Queries filter and sort by the sampling time (``sample_datetime``, the
    latest sample of the mixture) and return both times; the gap between them
    is how long the sample was stored. Filters by ``site_id`` or ``site_name``
    match records whose mixture holds a sample from those sites, so a blend of
    two sites shows up under both.

    Identical results are valid replicates (eg, a triplicate "not detected");
    only the record id tells them apart.

    :param name: database name
    :type name: str
    :param alias: short alias
    :type alias: str, optional

    :Example:

    .. code-block:: python

        db.insert_samples(
            dataframe=pd.DataFrame(
                {"name": ["B1", "B2"], "site_name": ["Gauge 1", "Gauge 2"],
                 "datetime": ["2024-03-01 12:00", "2024-03-01 15:00"]}
            )
        )
        # one mixture per sample, named after it
        db.insert_mixtures(dataframe=pd.DataFrame({"sample_name": ["B1", "B2"]}))
        db.insert_records(
            dataframe=pd.DataFrame(
                {"mixture_name": ["B1", "B2"], "value": [7.1, 6.8],
                 "datetime": ["2024-03-04", None]}
            ),
            spec_name="PH_LAB",
            flag=1,
        )
        df = db.query_records(query_dict={"site_name": "Gauge 1"})
    """

    # this is /src/plans/data/sql/lab (samples, mixtures, links and records)
    SQL_DIR = DATA_SQL_DIR / "lab"

    _TABLES = _TABLE_ORDER[:-1] + ("samples", "mixtures", "mixture_samples", "records")

    _FEATURE_KEY = "mixture_id"
    _KEY_TABLE = "mixtures"
    _QUERY_KEYS = DataBase._QUERY_KEYS + (
        "mixture_id",
        "mixture_name",
        "site_id",
        "site_name",
    )
    _ORDER_BY = ("spec_id", "sample_datetime", "mixture_id", "datetime")
    _TIME_SQL = "m.sample_datetime"
    _EPOCH_OUTPUT = DataBase._EPOCH_OUTPUT + ("sample_datetime",)
    _WIDE_INDEX = "sample_datetime"

    # SAMPLES AND MIXTURES
    # -------------------------------------------------------------------
    def insert_samples(self, dataframe):
        """
        Insert field samples.

        :param dataframe: one row per sample with ``name``, ``datetime`` (sampling
            time) and ``site_id`` or ``site_name``; ``alias`` and ``abstract``
            are optional
        :type dataframe: pandas.DataFrame
        :return: None
        :rtype: None
        :raises ValueError: if a required column is missing or a site is unknown
        """
        df = dataframe.copy()
        if "site_id" not in df.columns and "site_name" in df.columns:
            ids = self._resolve_names(names=df["site_name"], table=self._LAYER)
            df = df.drop(columns="site_name").assign(site_id=ids)
        missing = {"name", "datetime", "site_id"} - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
        df["datetime"] = self._to_epoch(series=df["datetime"])
        self.insert_rows(dataframe=df, on_table="samples")
        return None

    def insert_mixtures(self, dataframe):
        """
        Insert mixtures with the samples they hold.

        Each row links one sample to one mixture, so a blend of three samples
        takes three rows with the same mixture ``name``. Without a ``name``
        column, each sample becomes its own mixture, named after the sample
        (the common case of no mixing).

        :param dataframe: rows with ``sample_name`` or ``sample_id``, and optional
            ``name`` (mixture) and ``abstract`` (the first one per mixture is kept)
        :type dataframe: pandas.DataFrame
        :return: None
        :rtype: None
        :raises ValueError: if samples are missing or unknown
        """
        df = dataframe.copy()
        samples = self._name_lookup(table="samples")
        if "sample_id" not in df.columns:
            if "sample_name" not in df.columns:
                raise ValueError("Provide sample_name or sample_id")
            df["sample_id"] = self._resolve_names(
                names=df["sample_name"], table="samples"
            )
        if "name" not in df.columns:
            names = {i: n for n, i in samples.items()}
            df["name"] = df["sample_id"].map(names)
            if df["name"].isna().any():
                raise ValueError("Unknown sample_id value(s)")
        mixtures = df.drop_duplicates(subset="name")
        mixtures = mixtures[[c for c in ("name", "abstract") if c in df.columns]]
        # one block: no mixture is left without its samples
        with self.transaction():
            self.insert_rows(dataframe=mixtures, on_table="mixtures")
            ids = self._name_lookup(table="mixtures")
            links = pd.DataFrame(
                {"mixture_id": df["name"].map(ids), "sample_id": df["sample_id"]}
            )
            self.insert_rows(dataframe=links, on_table="mixture_samples")
        return None

    # QUERY
    # -------------------------------------------------------------------
    def _query_source(self):
        # records with the latest sampling time of their mixture (alias m)
        return (
            "SELECT r.*, s.name AS spec_name, s.scale, s.offset, m.sample_datetime "
            "FROM records r JOIN specs s ON r.spec_id = s.id "
            "LEFT JOIN (SELECT ms.mixture_id AS mixture_ref, "
            "MAX(sa.datetime) AS sample_datetime FROM mixture_samples ms "
            "JOIN samples sa ON sa.id = ms.sample_id GROUP BY ms.mixture_id) m "
            "ON m.mixture_ref = r.mixture_id"
        )

    def _query_filters(self, query_dict):
        """
        Build the WHERE conditions of :meth:`query_records`, adding site keys.

        ``site_id`` and ``site_name`` match records whose mixture holds at
        least one sample from those sites.

        :param query_dict: validated query keys
        :type query_dict: dict
        :return: SQL conditions (combined with AND) and their bound parameters
        :rtype: tuple[list[str], list]
        """
        conditions, params = super()._query_filters(query_dict=query_dict)
        sites = []
        if query_dict.get("site_id") is not None:
            sites.append(
                [operator.index(i) for i in self._as_list(query_dict["site_id"])]
            )
        if query_dict.get("site_name") is not None:
            sites.append(
                self._resolve_names(names=query_dict["site_name"], table=self._LAYER)
            )
        for ids in sites:
            conditions.append(
                "r.mixture_id IN (SELECT ms.mixture_id FROM mixture_samples ms "
                "JOIN samples sa ON sa.id = ms.sample_id "
                "WHERE sa.site_id IN (SELECT value FROM json_each(?)))"
            )
            params.append(json.dumps(ids))
        return conditions, params
