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
        "name": "ppt_monthly_chirps",
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

Values in ``records`` are stored as ``stored = actual * scale + offset``.
"""


# todo next steps

"""
DataBase() naturally evolves to the Semi-Spatial DataBase

SemiSpatialDB()
Expected to hold spatial information.
Geometries are not materialized in the database itself.

Example for a great case: H3 indexing.
All other cases when the spatial join can be left outside.

This includes the in the record.values:
geometry_id INTEGER NOT NULL.

Then this evolves to the SpatialDB()
A true spatial DB holds the spatial information on a spatial
table. The geometry is materialized.

This requires the 'geometries' table with at least:

id 
geometry (actual geometry)

This is deployed first via geopandas during creation.
The user must provide the layer with all extra columns
in the config.toml file.

Like : spatial: file and layer (gpkg path and layer name)

This then spreads over
SitesDB() for point based
PathsDB() for line based
ZonesDB() for polygon based

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
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
import pandas as pd

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
}


class DataBase(MbaE):
    """
    Base SQLite database with a structured schema.

    Manages catalogue and operational tables for hydro-environmental datasets.
    Child classes inherit and extend this via :attr:`SQL_DIR` and override
    methods where the schema diverges.

    :param name: database name
    :type name: str
    :param alias: short alias
    :type alias: str, optional
    """

    # this is /src/plans/data/sql/base
    SQL_DIR = DATA_SQL_DIR / "base"

    def __init__(self, name, alias=None):
        super().__init__(name, alias)

        # default catalogue files shipped with the package
        self.variables_default = DATA_CATALOGS_DIR / "variables.csv"
        self.flags_default = DATA_CATALOGS_DIR / "flags.csv"
        self.statistics_default = DATA_CATALOGS_DIR / "statistics.csv"
        self.sources_default = DATA_CATALOGS_DIR / "sources.csv"

        self.conn = None  # active sqlite3.Connection

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
                lines.append(f"  [{sid}] {name}")
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

    def execute_sql(self, sql):
        """
        Execute SQL from a string or a ``.sql`` file path.

        :param sql: SQL text or path to a file with ``.sql`` extension
        :type sql: str or Path
        :return: None
        :rtype: None
        """
        path = Path(sql)
        if path.suffix == ".sql" and path.is_file():
            sql_text = path.read_text(encoding="utf-8")
        else:
            sql_text = str(sql)
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

        Example — convert epoch to a readable UTC string directly in SQLite::

            df = db.query_sql(
                sql="SELECT datetime(datetime, 'unixepoch') AS dt, value FROM records LIMIT 10"
            )
        """
        path = Path(sql)
        if path.suffix == ".sql" and path.is_file():
            sql_text = path.read_text(encoding="utf-8")
        else:
            sql_text = str(sql)
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
        :raises FileNotFoundError: if the specs file does not exist
        """
        cfg = self.parse_setup(setup=config)
        file_db = Path(cfg["database"]["path"])
        if file_db.exists():
            if not overwrite:
                raise FileExistsError(f"Database already exists: {file_db}")
            file_db.unlink()

        try:
            self.connect(file_db=file_db)

            # create all tables in dependency order
            for table in _TABLE_ORDER:
                self.execute_sql(sql=self.SQL_DIR / f"{table}.sql")

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
        # convert a text/datetime series to integer epoch seconds; null values become None
        if pd.api.types.is_integer_dtype(series):
            return series
        converted = pd.to_datetime(arg=series, utc=True, errors="coerce")
        return converted.apply(lambda x: int(x.timestamp()) if pd.notna(x) else None)

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

    def insert_rows(self, dataframe, on_table, columns_map=None):
        """
        Insert DataFrame rows into a table, keeping only columns that exist in the target.

        :param dataframe: source data
        :type dataframe: pandas.DataFrame
        :param on_table: target table name
        :type on_table: str
        :param columns_map: column mapping ``{db_col: csv_name_or_index}``; values may be
            a string (source column name) or an int (source column position, 0-based)
        :type columns_map: dict, optional
        :return: None
        :rtype: None
        """
        df = dataframe.copy()
        if columns_map:
            df = self._apply_columns_map(df=df, columns_map=columns_map)
        cursor = self.conn.execute(f"PRAGMA table_info({on_table})")
        table_cols = {row[1] for row in cursor.fetchall()}
        df = df[[c for c in df.columns if c in table_cols]]
        df.to_sql(name=on_table, con=self.conn, if_exists="append", index=False)
        return None

    def insert_row(self, row_dict, on_table, columns_map=None):
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
        self.insert_rows(dataframe=df, on_table=on_table, columns_map=columns_map)
        return None

    def insert_records(
        self,
        dataframe,
        spec_id,
        flag=None,
        columns_map=None,
        transform_values=True,
        fill_nan=None,
    ):
        """
        Insert records into the ``records`` table for a given spec.

        ``spec_id`` is broadcast to all rows in the batch. The ``datetime``
        column is converted from text to epoch seconds automatically. The
        optional linear transform (``stored = actual * scale + offset``) is
        resolved from the matching row in ``specs``.

        NaN handling in ``value`` is controlled by ``fill_nan``: ``None`` drops
        rows with NaN values; any other value fills them before inserting.

        :param dataframe: source data; must contain at least ``datetime`` and ``value``;
            ``flag_value`` is also required unless ``flag`` is provided
        :type dataframe: pandas.DataFrame
        :param spec_id: foreign key referencing the ``specs`` table
        :type spec_id: int
        :param flag: if given, overwrite or create the ``flag_value`` column with this constant
        :type flag: int, optional
        :param columns_map: column mapping ``{db_col: csv_name_or_index}``; values may be
            a string (source column name) or an int (source column position, 0-based)
        :type columns_map: dict, optional
        :param transform_values: apply linear transform if True
        :type transform_values: bool
        :param fill_nan: fill value for NaN entries in ``value``; if ``None``, NaN rows are dropped
        :type fill_nan: float or None
        :return: None
        :rtype: None
        """
        df = dataframe.copy()
        if columns_map:
            df = self._apply_columns_map(df=df, columns_map=columns_map)
        required = {"datetime", "value"}
        if flag is None:
            required.add("flag_value")
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
        df["spec_id"] = spec_id
        if flag is not None:
            df["flag_value"] = flag
        df["datetime"] = self._to_epoch(series=df["datetime"])
        if fill_nan is None:
            df = df.dropna(subset=["value"])
        else:
            df["value"] = df["value"].fillna(fill_nan)
        if transform_values and "value" in df.columns:
            row = self.conn.execute(
                "SELECT scale, offset FROM specs WHERE id = ?", (spec_id,)
            ).fetchone()
            if row:
                scale, offset = row
                df["value"] = df["value"] * scale + offset
        self.insert_rows(dataframe=df, on_table="records")
        return None

    def insert_record(
        self,
        row_dict,
        spec_id,
        flag=None,
        columns_map=None,
        transform_values=True,
        fill_nan=None,
    ):
        """
        Insert a single record from a plain dict.

        Convenience wrapper around :meth:`insert_records` for one-row inserts.

        :param row_dict: record fields, e.g. ``{"datetime": "2024-01-01", "value": 12.3}``
        :type row_dict: dict
        :param spec_id: foreign key referencing the ``specs`` table
        :type spec_id: int
        :param flag: if given, overwrite or create the ``flag_value`` column with this constant
        :type flag: int, optional
        :param columns_map: column mapping ``{db_col: csv_name_or_index}``; values may be
            a string (source column name) or an int (source column position, 0-based)
        :type columns_map: dict, optional
        :param transform_values: apply linear transform if True
        :type transform_values: bool
        :param fill_nan: fill value for NaN entries in ``value``; if ``None``, NaN rows are dropped
        :type fill_nan: float or None
        :return: None
        :rtype: None
        """
        self.insert_records(
            dataframe=pd.DataFrame([row_dict]),
            spec_id=spec_id,
            flag=flag,
            columns_map=columns_map,
            transform_values=transform_values,
            fill_nan=fill_nan,
        )
        return None

    def load_records(
        self,
        files,
        spec_id,
        sep=None,
        flag=None,
        columns_map=None,
        transform_values=True,
        fill_nan=None,
    ):
        """
        Load records from a list of CSV files into the ``records`` table.

        All files are read and concatenated, then inserted via
        :meth:`insert_records`. See that method for column requirements and
        transform behaviour.

        :param files: paths to CSV files to load
        :type files: list[str or Path]
        :param spec_id: foreign key referencing the ``specs`` table
        :type spec_id: int
        :param sep: column separator; ``None`` uses :attr:`file_csv_sep`
        :type sep: str, optional
        :param flag: if given, overwrite or create the ``flag_value`` column with this constant
        :type flag: int, optional
        :param columns_map: column mapping ``{db_col: csv_name_or_index}``; values may be
            a string (source column name) or an int (source column position, 0-based)
        :type columns_map: dict, optional
        :param transform_values: apply linear transform if True
        :type transform_values: bool
        :param fill_nan: fill value for NaN entries in ``value``; if ``None``, NaN rows are dropped
        :type fill_nan: float or None
        :return: None
        :rtype: None
        """
        _sep = sep if sep is not None else self.file_csv_sep
        frames = [pd.read_csv(filepath_or_buffer=Path(f), sep=_sep) for f in files]
        df_all = pd.concat(objs=frames, ignore_index=True)
        self.insert_records(
            dataframe=df_all,
            spec_id=spec_id,
            flag=flag,
            columns_map=columns_map,
            transform_values=transform_values,
            fill_nan=fill_nan,
        )
        return None

    def query_records(self, query_dict=None, quiet=True):
        """
        Query the ``records`` table with optional filters combined with AND logic.

        Filters and options are passed as a single dict so the interface stays
        stable as new keys are added. All keys are optional; an empty or absent
        dict returns the full table.

        Supported keys:

        - ``start`` (*str*) — lower datetime bound (inclusive); any format parseable by pandas
        - ``end`` (*str*) — upper datetime bound (inclusive)
        - ``flag_value`` (*int* or *list[int]*) — one or more flag values to include
        - ``spec_id`` (*int* or *list[int]*) — one or more spec IDs to include
        - ``transform_values`` (*bool*, default ``True``) — reverse the linear transform
          so ``value`` holds actual values via ``actual = (stored - offset) / scale``
        The returned ``datetime`` column is always a timezone-aware (UTC) pandas datetime series.

        :param query_dict: filter and option keys (see above)
        :type query_dict: dict, optional
        :param quiet: if ``False``, prints elapsed query time to stdout
        :type quiet: bool
        :return: matching rows with ``datetime`` as UTC-aware pandas Timestamps
        :rtype: pandas.DataFrame
        """
        q = query_dict or {}
        start = q.get("start")
        end = q.get("end")
        flag_value = q.get("flag_value")
        spec_id = q.get("spec_id")
        transform_values = q.get("transform_values", True)

        conditions = []
        params = []

        if start is not None:
            conditions.append("r.datetime >= ?")
            params.append(int(pd.Timestamp(start, tz="UTC").timestamp()))

        if end is not None:
            conditions.append("r.datetime <= ?")
            params.append(int(pd.Timestamp(end, tz="UTC").timestamp()))

        if flag_value is not None:
            vals = [flag_value] if isinstance(flag_value, int) else list(flag_value)
            conditions.append(f"r.flag_value IN ({','.join('?' * len(vals))})")
            params.extend(vals)

        if spec_id is not None:
            ids = [spec_id] if isinstance(spec_id, int) else list(spec_id)
            conditions.append(f"r.spec_id IN ({','.join('?' * len(ids))})")
            params.extend(ids)

        sql = "SELECT r.*, s.scale, s.offset FROM records r JOIN specs s ON r.spec_id = s.id"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        t0 = time.perf_counter()
        df = pd.read_sql(sql=sql, con=self.conn, params=params)
        elapsed = time.perf_counter() - t0

        df["datetime"] = pd.to_datetime(df["datetime"], unit="s", utc=True)
        df["inserted"] = pd.to_datetime(df["inserted"], unit="s", utc=True)
        if transform_values:
            df["value"] = (df["value"] - df["offset"]) / df["scale"]
        df = df.drop(columns=["scale", "offset"])
        if not quiet:
            print(f"[query_records] {len(df)} rows in {elapsed:.3f}s")
        return df
