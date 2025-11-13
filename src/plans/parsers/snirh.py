# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Parse data from ``SNIRH`` Hidroweb files (Brazillian offical hydrological database)

Overview
--------

# todo [major docstring improvement] -- overview
Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl. Pellentesque habitant morbi tristique senectus
et netus et malesuada fames ac turpis egestas.

Example
-------

# todo [major docstring improvement] -- examples
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam,
in porttitor lacus lobortis vitae. In a lacinia nisl.

.. code-block:: python

    import numpy as np
    print("Hello World!)

Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl. Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl.
"""

import pandas as pd

# todo ---- improve examples an docstrings
# todo ---- format module
# todo ---- refactor better names
# todo ---- refactor for root.DataSet inheritance
# todo ---- make unit tests


class Stage:
    # todo [major doctring]
    def __init__(self, name="MyStage"):
        # todo [doctring]
        # Object attributes
        self.name = name
        self.dtfield = "datetime"
        self.varfield = "h"
        self.prefix = "snirh_stage"

        # data
        self.station_metadata_df = None
        self.data = None
        self.start_data = None
        self.end_data = None

        # reading
        self.reading_metadata_splitter = ": "
        self.reading_delimiter = ";"
        self.reading_decimals = "."
        self.reading_skiprows = 15  # len(self.station_metadata) + 1
        self.reading_dtfields = ["Data", "hora"]
        self.reading_encoding = "utf-8"
        self.reading_dtformat = "%d/%m/%Y %H:%M:%S"
        self.reading_nan = ["null", -9999]
        self.reading_stage_fields = [
            "Cota01",
            "Cota02",
            "Cota03",
            "Cota04",
            "Cota05",
            "Cota06",
            "Cota07",
            "Cota08",
            "Cota09",
            "Cota10",
            "Cota11",
            "Cota12",
            "Cota13",
            "Cota14",
            "Cota15",
            "Cota16",
            "Cota17",
            "Cota18",
            "Cota19",
            "Cota20",
            "Cota21",
            "Cota22",
            "Cota23",
            "Cota24",
            "Cota25",
            "Cota26",
            "Cota27",
            "Cota28",
            "Cota29",
            "Cota30",
            "Cota31",
        ]

    def load_data(self, file_path):
        """
        Load data from incoming data

        :param file_path: ``.csv`` file path
        :type file_path: str
        :return: None
        :rtype: None
        """
        self.data = self.read_data(file_path=file_path)
        # self.update()
        return None

    def read_data(self, file_path):
        """
        Handle data import

        :param file_path: ``.csv`` file path
        :type file_path: str
        :return: DataFrame
        :rtype: pandas.DataFrame
        """

        # load station_metadata first
        # self.load_metadata(file_path=file_path)

        # Read data using pandas, specifying the data type of the 'Hora Medicao' column as a string
        df = pd.read_csv(
            file_path,
            skiprows=self.reading_skiprows,
            delimiter=self.reading_delimiter,
            dtype={e: str for e in self.reading_dtfields},
            decimal=self.reading_decimals,
            encoding=self.reading_encoding,
            na_values=self.reading_nan,
        )

        # fill void hour fields
        df[self.reading_dtfields[1]] = df[self.reading_dtfields[1]].fillna("12:00")
        # concat seconds to hour field
        df[self.reading_dtfields[1]] = df[self.reading_dtfields[1]] + ":00"

        # filter columns
        lst_colunms = self.reading_dtfields + self.reading_stage_fields
        df = df[lst_colunms]

        # filter hour (only 12:00:00)
        df = df.query("hora == '12:00:00'").copy()

        # Combine 'Data' and 'hora' columns into a single datetime field
        df[self.dtfield] = pd.to_datetime(
            df[self.reading_dtfields[0]] + " " + df[self.reading_dtfields[1]],
            format=self.reading_dtformat,
        )

        # Drop the original columns
        df.drop(self.reading_dtfields, axis=1, inplace=True)

        # Reorganize columns with 'DateTime' at the beginning
        columns = [self.dtfield] + [column for column in df if column != self.dtfield]

        # Apply the column reorganization
        df = df[columns]

        # Clear void rows
        df = df.dropna(subset=df.columns[1:], how="all")

        # Reshape the dataframe
        df_melted = pd.melt(
            df, id_vars=[self.dtfield], var_name="Day", value_name=self.varfield
        )

        # Extract day number from 'Cota' columns
        df_melted["Day"] = df_melted["Day"].str.extract(r"(\d+)").astype(int)

        # Create a new DateTime column for each day
        df_melted[self.dtfield] = df_melted.apply(
            lambda row: row[self.dtfield] + pd.Timedelta(days=row["Day"] - 1), axis=1
        )

        # Drop the 'Day' column as it's no longer needed
        df_melted.drop(columns=["Day"], inplace=True)

        # Sort by the new DateTime column
        df_melted.sort_values(by=self.dtfield, inplace=True)

        df_melted.drop_duplicates(subset=[self.dtfield], inplace=True)

        # Reset index
        df_melted.reset_index(drop=True, inplace=True)
        # Clear void rows
        df_melted = df_melted.dropna(subset=df_melted.columns[1:], how="all")

        return df_melted


if __name__ == "__main__":
    print("Hello world!")
    # todo [testing]
    """
    d = "C:/gis/snirh/rhn/src/Estacao_87382000_CSV_2025-02-27T18_02_48.292Z"
    f = f"{d}/87382000_Cotas.csv"
    c = Stage(name="SaoLeo")
    c.load_data(file_path=f)

    print(c.data.columns)
    print(c.data[c.data.columns[:10]].head(4).to_string())
    print(c.data[c.data.columns[:10]].tail(4).to_string())

    c.data.to_csv(
        "C:/gis/snirh/rhn/data/tier1/snirh_ana_87382000_DTS19730725-DTE20240630.csv",
        sep=";",
        encoding="utf-8",
    )
    plt.plot(c.data["DateTime"], c.data["Stage"], ".")
    plt.show()
    """
