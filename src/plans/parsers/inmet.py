# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Parse data from ``INMET`` files (Brazillian Meteorological Office)

Overview
--------

# todo [major docstring improvement] -- overview
Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl. Pellentesque habitant morbi tristique senectus
et netus et malesuada fames ac turpis egestas.

Example
-------

"""

import pandas as pd

# todo ---- improve examples an docstrings
# todo ---- format module
# todo ---- refactor better names
# todo ---- refactor for root.DataSet inheritance
# todo ---- make unit tests


class _StationINMET_:
    """
    This is a base object for parsing Inmet Stations datasets

    Objects downstream will use or overwrite this methods

    """

    def __init__(self, name="MyStationINMET"):
        """Initialization method

        :param name: name of station
        :type name: str
        """
        # Object attributes
        self.name = name
        self.dtfield = "datetime"
        self.prefix = "inmet"

        # base glossary
        self.gls = {
            "CH (NUVENS ALTAS)(codigo)": "ch",
            "PRECIPITACAO TOTAL, HORARIO(mm)": "p",
            "VISIBILIDADE, HORARIA(codigo)": "vis",
        }

        # data strucutre attributes
        d1, d2 = self._metadata_util()
        self.station_metadata = d1
        self.station_metadata_df = None
        self.glossary = self.get_glossary()
        self.data = None
        self.start_data = None
        self.end_data = None

        # reading attributes
        self.reading_metadata_splitter = ": "
        self.reading_delimiter = ";"
        self.reading_decimals = "."
        self.reading_skiprows = len(self.station_metadata) + 1
        self.reading_dtfields = ["Data Medicao", "Hora Medicao"]
        self.reading_encoding = "utf-8"
        self.reading_dtformat = "%Y-%m0-%d %H:%M:%S"
        self.reading_nan = ["null", -9999]

    def get_metadata(self):
        """
        Base metata getter method

        :return: dictionary of metadata
        :rtype: dict
        """
        dict_meta = {"Name": self.name, "Start": self.start_data, "End": self.end_data}
        dict_meta.update(self.station_metadata)
        return dict_meta

    def update(self):
        """
        Base update method

        :return: None
        :rtype: None
        """
        # update start and end dates
        if self.data is not None:
            self.start_data = self.data[self.dtfield].min()
            self.end_data = self.data[self.dtfield].max()
        return None

    def _metadata_util(self):
        """Utility method for naming conversions

        :return: utility dictionaries
        :rtype: dict, dict
        """
        d = {
            "station_name": [None, "NOME"],
            "station_id": [None, "CODIGOESTACAO"],
            "station_y": [None, "Latitude"],
            "station_x": [None, "Longitude"],
            "station_z": [None, "Altitude"],
            "station_status": [None, "Situacao"],
            "station_start": [None, "DataInicial"],
            "station_end": [None, "DataFinal"],
            "timescale": [None, "PeriodicidadedaMedicao"],
        }
        d1 = {}
        d2 = {}
        for k in d:
            d1[k] = d[k][0]
            d2[d[k][1]] = k
        return d1, d2

    def _standardize_metadata_fields(self, metadata):
        """Utility method for standardizing metadata fields

        :param metadata: dictionary of incoming metadata
        :type metadata: dict
        :return: new standard metatada dictionary
        :rtype: dict
        """
        dict_1, dict_convert = self._metadata_util()
        new_metadata = {}
        for k in dict_convert:
            new_metadata[dict_convert[k]] = metadata[k]
        return new_metadata

    def _get_columns_gls(self):
        """Retrieve the glossary mapping and its mirror.

        :return: A tuple containing the glossary mapping and its mirror.
        :rtype: tuple[dict, dict]
        """
        # compute the opposite
        inverse_mapping = {v: k for k, v in self.gls.items()}
        return self.gls, inverse_mapping

    def get_glossary(self):
        """Generate a glossary DataFrame from the stored glossary mapping.

        :return: A DataFrame containing field names and their source descriptions.
        :rtype: class.`pandas.DataFrame`
        """
        a, b = self._get_columns_gls()
        df = pd.DataFrame(
            {"Field": [a[k] for k in a], "SourceDescription": [k for k in a]}
        )
        return df

    def fix_text(self, text, remove_spaces=False):
        """Standardize text by converting to uppercase and replacing specific characters.

        :param text: The inputs text to be processed.
        :type text: str
        :param remove_spaces: Whether to remove spaces from the text.
        :type remove_spaces: bool, optional
        :return: The processed text.
        :rtype: str
        """
        text = text.upper()
        # Iterate through each line and replace problematic characters
        text = text.replace("?", "A")
        text = text.replace("Ç", "C")
        text = text.replace("Á", "A")
        text = text.replace("Ã", "A")
        text = text.replace("Í", "I")
        text = text.replace("É", "E")
        text = text.replace("(YYYY-MM-DD)", "")
        if remove_spaces:
            text = text.replace(" ", "")
        return text

    def read_metadata(self, file_path):
        """Read station metadata from a file and return it as a dictionary.

        :param file_path: Path to the metadata file.
        :type file_path: str
        :return: Dictionary containing metadata fields and values.
        :rtype: dict
        """
        # Read station_metadata
        with open(file_path, "r") as file:
            # Read lines until a blank line is encountered, indicating the end of station_metadata
            metadata = {}
            for line in file:
                if line.strip() == "" or len(line.strip()) > 50:
                    break
                key, value = line.strip().split(self.reading_metadata_splitter)
                value = value.replace(",", ".")  # fix decimals
                key = self.fix_text(text=key, remove_spaces=True)
                metadata[key] = value
        # standardize fields
        metadata = self._standardize_metadata_fields(metadata=metadata)
        return metadata

    def load_metadata(self, file_path):
        """Load station metadata from a file and store it in a DataFrame.

        :param file_path: Path to the metadata file.
        :type file_path: str
        :return: None
        :rtype: None
        """
        self.station_metadata = self.read_metadata(file_path)
        self.station_metadata_df = pd.DataFrame(
            {
                "Field": [k for k in self.station_metadata],
                "Value": [self.station_metadata[k] for k in self.station_metadata],
            }
        )
        return None

    def read_data(self, file_path):
        """read all data from file

        :param file_path: file path
        :type file_path: str
        :return: pandas dataframe
        :rtype: class.`pandas.DataFrame`
        """

        # load station_metadata first
        self.load_metadata(file_path=file_path)
        print(self.station_metadata_df)
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

        # handle void case
        if len(df) > 0:
            # Combine 'Data Medicao' and 'Hora Medicao' columns into a single datetime field
            if len(self.reading_dtfields) > 1:
                df[self.dtfield] = pd.to_datetime(
                    df[self.reading_dtfields[0]].str.split().str[0]
                    + " "
                    + df[self.reading_dtfields[1]].str.split().str[0],
                    format=self.reading_dtformat,
                )
            else:
                df[self.dtfield] = pd.to_datetime(
                    df[self.reading_dtfields[0]] + " 12:00:00",
                    format=self.reading_dtformat,
                )

            # Drop the original 'Data Medicao' and 'Hora Medicao' columns
            df.drop(self.reading_dtfields, axis=1, inplace=True)

            # Reorganize columns with 'DateTime' at the beginning
            columns = [self.dtfield] + [
                column for column in df if column != self.dtfield
            ]

            # Apply the column reorganization
            df = df[columns]

            # Check and eliminate the last column if it doesn't have a name
            if "Unnamed" in columns[-1]:
                df = df.iloc[:, :-1]

            fix_names = {}
            for c in df.columns[1:]:
                fix_names[c] = self.fix_text(c)
            # Rename columns in the DataFrame
            df.rename(columns=fix_names, inplace=True)

            # get new colum names
            simplified_names, inverse_mapping = self._get_columns_gls()

            # Rename columns in the DataFrame
            df.rename(columns=simplified_names, inplace=True)

            # Clear void rows
            df = df.dropna(subset=df.columns[1:], how="all")

            return df
        else:
            return None

    def load_data(self, file_path):
        """Load data from a file and update the instance.

        :param file_path: Path to the data file.
        :type file_path: str
        :return: None
        :rtype: None
        """
        self.data = self.read_data(file_path=file_path)
        self.update()
        return None

    def export_data(self, folder, append_id=True):
        """Export the data to a CSV file.

        :param folder: Folder where the file will be saved.
        :type folder: str
        :param append_id: Whether to append the station ID to the filename.
        :type append_id: bool, optional
        :return: Path to the exported file.
        :rtype: str
        """
        dts = self.start_data.strftime("%Y%m0%d%H")
        dte = self.end_data.strftime("%Y%m0%d%H")
        filename = "{}_{}_DTS{}-DTE{}.csv".format(
            self.prefix, self.station_metadata["station_id"], dts, dte
        )
        file_path = "{}/{}".format(folder, filename)

        _df = self.data.copy()
        _cols = list(_df.columns)
        if append_id:
            id_s = "record_id"
            _meta_df = self.station_metadata_df.copy()
            # Extracting the Value for Station_Code
            station_code = _meta_df.loc[
                _meta_df["Field"] == "station_id", "Value"
            ].values[0]
            _df["station_id"] = station_code
            # Create the ID field (Station_Code + YYYYMMDDHH)
            _df[id_s] = (
                _df["station_id"]
                + "DT"
                + _df["datetime"].dt.strftime("%Y%m0%d%H")
                + "0000"
            )
            # Arrange columns
            _new_cols = [id_s, "station_id"] + _cols[:]
            _df = _df[_new_cols].copy()
        _df.to_csv(file_path, sep=";", index=False)
        return file_path

    def export_metadata(self, folder):
        """Export station metadata to a CSV file.

        :param folder: Folder where the file will be saved.
        :type folder: str
        :return: Path to the exported metadata file.
        :rtype: str
        """
        filename = "{}_{}_info.csv".format(
            self.prefix, self.station_metadata["Station_Code"]
        )
        file_path = "{}/{}".format(folder, filename)
        self.station_metadata_df.to_csv(file_path, sep=";", index=False)
        return file_path

    def export_glossary(self, folder):
        """Export the glossary to a CSV file.

        :param folder: Folder where the file will be saved.
        :type folder: str
        :return: Path to the exported glossary file.
        :rtype: str
        """
        filename = "{}_{}_glossary.csv".format(
            self.prefix, self.station_metadata["Station_Code"]
        )
        file_path = "{}/{}".format(folder, filename)
        df = self.get_glossary()
        df.to_csv(file_path, sep=";", index=False)
        return file_path

    def export(self, folder):
        """Export data, metadata, and glossary to CSV files.

        :param folder: Folder where the files will be saved.
        :type folder: str
        :return: Dictionary containing paths to the exported files.
        :rtype: dict
        """
        f1 = self.export_data(folder=folder)
        f2 = self.export_metadata(folder=folder)
        f3 = self.export_glossary(folder=folder)
        return {"Data": f1, "Metadata": f2, "Glossary": f3}


# todo docstrings
class _Conventional_(_StationINMET_):

    # todo docstring
    def __init__(self, name="MyConvetional"):
        super().__init__(name=name)
        # overwrite super() attributes:
        self.prefix = "inmet_conv"

        self.gls = {
            "CH (NUVENS ALTAS)(codigo)": "ch",
            "VISIBILIDADE, HORARIA(codigo)": "vis",
        }
        self.glossary = self.get_glossary()

        # reading
        self.reading_metadata_splitter = ": "
        self.reading_delimiter = ";"
        self.reading_decimals = "."
        self.reading_skiprows = len(self.station_metadata) + 1
        self.reading_dtfields = ["DATA MEDICAO", "HORA MEDICAO"]

    def _metadata_util(self):
        d = {
            "station_name": [None, "NOME"],
            "station_code": [None, "CODIGOESTACAO"],
            "station_y": [None, "LATITUDE"],
            "station_x": [None, "LONGITUDE"],
            "station_z": [None, "ALTITUDE"],
            "station_status": [None, "SITUACAO"],
            "station_start": [None, "DATAINICIAL"],
            "station_End": [None, "DATAFINAL"],
            "timescale": [None, "PERIODICIDADEDAMEDICAO"],
        }
        d1 = {}
        d2 = {}
        for k in d:
            d1[k] = d[k][0]
            d2[d[k][1]] = k
        return d1, d2


# todo docstring
class ConventionalHourly(_Conventional_):

    # todo docstring
    def __init__(self, name="MyConvetionalHourly"):
        super().__init__(name=name)
        # overwrite super() attributes:
        self.prefix = "inmet_convh"
        self.gls = {
            "CH (NUVENS ALTAS)(CODIGO)": "ch",
            "CL (NUVENS BAIXAS)(CODIGO)": "cl",
            "CM (NUVENS MEDIAS)(CODIGO)": "cm",
            "NEBULOSIDADE, HORARIA(DECIMOS)": "neb",
            "PRECIPITACAO TOTAL, HORARIO(MM)": "p",
            "PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA(MB)": "pa_loc",
            "PRESSAO ATMOSFERICA AO NIVEL DO MAR, HORARIA(MB)": "pa_sea",
            "TEMPERATURA DO AR - BULBO SECO, HORARIA(°C)": "temp_db",
            "TEMPERATURA DO AR - BULBO UMIDO, HORARIA(°C)": "temp_wb",
            "TEMPERATURA DO PONTO DE ORVALHO(°C)": "temp_dp",
            "UMIDADE RELATIVA DO AR, HORARIA(%)": "rm",
            "VENTO, DIRECAO HORARIA(CODIGO)": "wd",
            "VENTO, VELOCIDADE HORARIA(M/S)": "ws",
            "VISIBILIDADE, HORARIA(CODIGO)": "vis",
        }

        # reading
        self.reading_dtfields = ["Data Medicao", "Hora Medicao"]
        self.reading_dtformat = "%Y-%m0-%d %H%M"


# todo docstring
class ConventionalDaily(_Conventional_):
    """
    Parser object for ``INMET`` Conventional Stations - Daily measurements.
    """

    # todo docstring
    def __init__(self, name="MyConvetionalDaily"):
        super().__init__(name=name)
        # overwrite super() attributes:
        self.prefix = "inmet_convd"
        self.gls = {
            "INSOLACAO TOTAL, DIARIO(H)": "ist",
            "EVAPORACAO DO PICHE, DIARIA(MM)": "evp",
            "PRECIPITACAO TOTAL, DIARIO(MM)": "p",
            "TEMPERATURA MAXIMA, DIARIA(°C)": "temp_max",
            "TEMPERATURA MEDIA COMPENSADA, DIARIA(°C)": "temp_mean",
            "TEMPERATURA MINIMA, DIARIA(°C)": "temp_min",
            "UMIDADE RELATIVA DO AR, MEDIA DIARIA(%)": "rm_mean",
            "UMIDADE RELATIVA DO AR, MINIMA DIARIA(%)": "rm_min",
            "VENTO, VELOCIDADE MEDIA DIARIA(M/S)": "ws_mean",
        }

        # reading
        self.reading_dtfields = ["Data Medicao"]
        self.reading_dtformat = "%Y-%m0-%d %H:%M:%S"


class _Automatic_(_StationINMET_):
    """
    Base Parser object for automatic INMET stations
    """

    def __init__(self, name="MyAutomatic"):
        super().__init__(name=name)
        # Object attributes
        self.prefix = "inmet_autoh"
        # reading specs
        self.reading_delimiter = ";"
        self.reading_skiprows = len(self.station_metadata)


class Automatic(_Automatic_):
    """
    Parser object for ``INMET`` Automatic Stations provided by any date range.
    """

    def __init__(self, name="MyAutomatic"):
        super().__init__(name=name)
        self.gls = {
            "PRECIPITACAO TOTAL, HORARIO(MM)": "p",
            "PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA(MB)": "pa_loc",
            "PRESSAO ATMOSFERICA REDUZIDA NIVEL DO MAR, AUT(MB)": "pa_sea",
            "PRESSAO ATMOSFERICA MAX.NA HORA ANT. (AUT)(MB)": "pa_loc_premax",
            "PRESSAO ATMOSFERICA MIN. NA HORA ANT. (AUT)(MB)": "pa_loc_premin",
            "RADIACAO GLOBAL(KJ/M²)": "rad",
            "TEMPERATURA DA CPU DA ESTACAO(°C)": "temp_cpu",
            "TEMPERATURA DO AR - BULBO SECO, HORARIA(°C)": "temp_db",
            "TEMPERATURA DO PONTO DE ORVALHO(°C)": "temp_db",
            "TEMPERATURA MAXIMA NA HORA ANT. (AUT)(°C)": "temp_db_premax",
            "TEMPERATURA MINIMA NA HORA ANT. (AUT)(°C)": "temp_db_premin",
            "TEMPERATURA ORVALHO MAX. NA HORA ANT. (AUT)(°C)": "temp_db_premax",
            "TEMPERATURA ORVALHO MIN. NA HORA ANT. (AUT)(°C)": "temp_db_premin",
            "TENSAO DA BATERIA DA ESTACAO(V)": "volt",
            "UMIDADE REL. MAX. NA HORA ANT. (AUT)(%)": "rm_premin",
            "UMIDADE REL. MIN. NA HORA ANT. (AUT)(%)": "rm_premax",
            "UMIDADE RELATIVA DO AR, HORARIA(%)": "rm",
            "VENTO, DIRECAO HORARIA (GR)(° (GR))": "wd",
            "VENTO, RAJADA MAXIMA(M/S)": "wg",
            "VENTO, VELOCIDADE HORARIA(M/S)": "ws",
        }
        # data
        d1, d2 = self._metadata_util()
        self.station_metadata = d1
        self.glossary = self.get_glossary()

        # reading
        self.reading_metadata_splitter = ": "
        self.reading_dtformat = "%Y-%m0-%d %H%M"

    def _metadata_util(self):
        d = {
            "station_name": [None, "NOME"],
            "station_id": [None, "CODIGOESTACAO"],
            "station_y": [None, "Latitude".upper()],
            "station_x": [None, "Longitude".upper()],
            "station_z": [None, "Altitude".upper()],
            "station_status": [None, "Situacao".upper()],
            "station_start": [None, "DataInicial".upper()],
            "station_end": [None, "DataFinal".upper()],
            "timescale": [None, "PeriodicidadedaMedicao".upper()],
        }
        d1 = {}
        d2 = {}
        for k in d:
            d1[k] = d[k][0]
            d2[d[k][1]] = k

        return d1, d2


if __name__ == "__main__":
    print("Hello")
    # todo [testing]
    """
    # file path
    f = "_inmet_auto_src.csv"

    # instantiate object
    auto = Automatic(name="Automatic Station")

    # load data
    auto.load_data(file_path=f)

    # print data (pandas dataframe)
    print(auto.data.head().to_string(index=False))

    # print metadata (pandas dataframe)
    print(auto.station_metadata_df.to_string())

    # export to folder
    auto.export_data(folder="C:/data", append_id=True)
    """
