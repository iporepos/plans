# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short module description (1-3 sentences)}
todo docstring

Features
--------
todo docstring

* {feature 1}
* {feature 2}
* {feature 3}
* {etc}

Overview
--------
todo docstring
{Overview description}

Examples
--------
todo docstring
{Examples in rST}

Print a message

.. code-block:: python

    # print message
    print("Hello world!")
    # [Output] >> 'Hello world!'


"""
# LOOP COMMENTS
# ***********************************************************************
# Launch, Observe, Optimize, Progress

# todo --- KISS improvements
#  main() can be improved by parsing a tools.csv file with all tools specs
#  stored in a smart way

# todo --- DRY refactor
#  implement a class-based (OOP) logic. This will reduce
#  severely the code repetition for every tool

# todo --- DOCS improvements
#  wait for major upgrades for developing consistent docstrings
#  include examples of how to call each tool in the terminal

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import time, logging
from pathlib import Path
import argparse

# ... {develop}

# External imports
# =======================================================================
import pandas as pd
import matplotlib.pyplot as plt

# ... {develop}

# Project-level imports
# =======================================================================
from plans.datasets import DC_NODATA, TimeSeries, AOI, Raster

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
from plans.config import parse_fields, parse_files

# ... {develop}

# CONSTANTS -- Module-level
# =======================================================================
logger = logging.getLogger(__name__)
LABEL_STARTING = "starting"
LABEL_LOADING = "loading"
LABEL_PROCESSING = "processing"
LABEL_EXPORTING = "exporting"
LABEL_RUN = "run"
LABEL_PROJECT = "project"

DC_MSG = {
    LABEL_LOADING: "loaded inputs",
    LABEL_PROCESSING: "processed data",
    LABEL_EXPORTING: "exported outputs",
    LABEL_RUN: "run completed",
}
# ... {develop}


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- utilities
# =======================================================================


def setup_logger(label, talk):
    s = "%(asctime)s [%(levelname)s] plans.tools.{}: %(message)s".format(label)
    logging.basicConfig(level=logging.INFO, format=s)
    logger.setLevel(logging.INFO if talk else logging.WARNING)


# step decorator
def step(label):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            logger.info(f"{label} ...")

            result = func(*args, **kwargs)  # <--- your unique protocol here

            elapsed = time.time() - start
            logger.info(format_msg_elapsed(DC_MSG[label], elapsed))
            return result, elapsed

        return wrapper

    return decorator


def format_msg_elapsed(msg, time):
    return "{} in {:.2f} seconds".format(msg, time)


def format_msg_output(folder):
    return "check results in:\n\n\t{}\n".format(folder)


def save_runtime_data(steps, times, folder_output):
    df_run = pd.DataFrame({"step": steps, "time": times})
    file_output_runtimes = Path(folder_output) / "runtimes.txt"
    df_run.to_csv(file_output_runtimes, sep=";", index=False)
    return file_output_runtimes


def parse_spatial_parameters(title, file_parameters):
    df_files = parse_files()
    file_name = df_files.loc[df_files["title"] == title, "name"].values[0]

    df_fields = parse_fields()
    df_fields = df_fields.query(f"{file_name} == 'w'").copy()
    ls_parameters = list(df_fields["name"].values)

    ls_fields_parameters = ["w_{}".format(p) for p in ls_parameters]

    # get parameter set
    # ---------------------------------------------------------------
    df_params = pd.read_csv(file_parameters, sep=";")
    df_params_filter = df_params[df_params["field"].isin(ls_parameters)]
    ls_upscaled_values = list(df_params_filter["value"])

    df_parameters = pd.DataFrame(
        {
            "field": ls_fields_parameters,
            "name": ls_parameters,
            "value": ls_upscaled_values,
            "units": list(df_fields["units"].values),
            "description": list(df_fields["description"].values),
        }
    )
    return df_parameters


def export_parameters(folder_output, parameters, basin, views, prefix, label):
    # todo docstring
    # export catalog
    # ---------------------------------------------------------------
    # todo output index add this file
    file_catalog = Path(folder_output) / f"{prefix}_parameters_catalog.csv"
    parameters.catalog.to_csv(file_catalog, sep=";", index=False)

    # export rasters
    # ---------------------------------------------------------------
    for k in parameters.collection:
        filename = parameters.collection[k].file_data
        logger.info(f"exporting maps >>> {label} {filename}.tif")
        parameters.collection[k].export_tif(folder=folder_output, filename=filename)
    # export views
    # ---------------------------------------------------------------
    if views:
        for k in parameters.collection:
            filename = parameters.collection[k].file_data
            logger.info(f"exporting figs >>> {label} {filename}.jpg")
            parameters.collection[k].view(show=False)
            parameters.collection[k].apply_aoi_mask(grid_aoi=basin.data)
            # mask by main basin
            filename2 = f"{filename}_main"
            logger.info(f"exporting figs >>> {label} {filename2}.jpg")
            s_title = parameters.collection[k].view_specs["title"]
            parameters.collection[k].view_specs["title"] = f"{s_title} | main basin"
            parameters.collection[k].view_specs["filename"] = filename2
            parameters.collection[k].view(show=False)
    return None


# FUNCTIONS -- Project-level
# =======================================================================


def demo(folder_output, file_input1, file_input2, talk):
    # todo docstring
    # LOGGING
    # -------------------------------------------------------------------
    tool_name = demo.__name__
    setup_logger(label=tool_name, talk=talk)

    # DEFINE PROTOCOLS
    # -------------------------------------------------------------------
    @step(LABEL_LOADING)
    def load_inputs(f1, f2):
        df1 = pd.read_csv(f1)
        df2 = pd.read_csv(f2)
        time.sleep(1)
        return df1, df2

    @step(LABEL_PROCESSING)
    def process_data(df1, df2):
        time.sleep(3)
        return pd.concat([df1, df2])

    @step(LABEL_EXPORTING)
    def export_data(df, folder):
        time.sleep(2)
        file_out = Path(folder) / "demo_output.csv"
        df.to_csv(file_out, sep=";", index=False)
        return file_out

    # START UP
    # -------------------------------------------------------------------
    start_total = time.time()
    ls_steps, ls_times = [], []
    logger.info(LABEL_STARTING)

    # LOADING INPUTS
    # -------------------------------------------------------------------
    (df1, df2), t = load_inputs(file_input1, file_input2)

    ls_steps.append(LABEL_LOADING)
    ls_times.append(t)

    # PROCESSING DATA
    # -------------------------------------------------------------------
    df_out, t = process_data(df1, df2)

    ls_steps.append(LABEL_PROCESSING)
    ls_times.append(t)

    # EXPORTING OUTPUTS
    # -------------------------------------------------------------------
    file_out, t = export_data(df_out, folder_output)

    ls_steps.append(LABEL_EXPORTING)
    ls_times.append(t)

    # SHUTDOWN
    # -------------------------------------------------------------------
    total_elapsed = time.time() - start_total
    logger.info(format_msg_elapsed(DC_MSG[LABEL_RUN], total_elapsed))
    logger.info(format_msg_output(folder_output))

    # record it in your steps/times lists
    ls_steps.append(LABEL_RUN)
    ls_times.append(total_elapsed)

    # Save all runtime data including total
    runtimes_file = save_runtime_data(
        steps=ls_steps, times=ls_times, folder_output=folder_output
    )
    return True


def analysis_dto(folder_output, file_ldd, file_basin, label, views, talk):
    # todo docstring
    from plans.datasets import LDD, DTO
    from plans.geo import distance_to_outlet

    # LOGGING
    # -------------------------------------------------------------------
    tool_name = analysis_dto.__name__
    setup_logger(label=tool_name, talk=talk)

    # DEFINE PROTOCOLS
    # -------------------------------------------------------------------
    @step(LABEL_LOADING)
    def load_inputs(file_ldd, file_basin):
        # handle ldd
        ldd = LDD(name=label)
        ldd.load_data(file_data=file_ldd)

        # handle basin
        basin = None
        if file_basin is not None:
            basin = AOI(name=label)
            basin.load_data(file_data=file_basin)

        return ldd, basin

    @step(LABEL_PROCESSING)
    def process_data(ldd):
        grd_outdist = distance_to_outlet(grd_ldd=ldd.data, n_res=ldd.cellsize)
        return grd_outdist

    @step(LABEL_EXPORTING)
    def export_data(ldd, basin, grd_outdist):
        file_name_output = "dto"
        # setup output object
        dto = DTO(name=label)
        dto.data = grd_outdist.copy()
        dto.raster_metadata = ldd.raster_metadata
        dto.raster_metadata["NODATA_value"] = DC_NODATA["float32"]
        # apply aoi mask
        if basin is not None:
            dto.apply_aoi_mask(grid_aoi=basin.data, inplace=True)

        if views:
            dto.view_specs["folder"] = folder_output
            dto.view_specs["filename"] = file_name_output
            dto.view(show=False)
        file_output = dto.export_tif(folder=folder_output, filename=file_name_output)
        return file_output

    # START UP
    # -------------------------------------------------------------------
    start_total = time.time()
    ls_steps, ls_times = [], []
    logger.info(LABEL_STARTING)

    # LOADING INPUTS
    # -------------------------------------------------------------------
    (ldd, basin), t = load_inputs(file_ldd, file_basin)

    ls_steps.append(LABEL_LOADING)
    ls_times.append(t)

    # PROCESSING DATA
    # -------------------------------------------------------------------
    grd_outdist, t = process_data(ldd)

    ls_steps.append(LABEL_EXPORTING)
    ls_times.append(t)

    # EXPORTING OUTPUTS
    # -------------------------------------------------------------------
    file_output, t = export_data(ldd, basin, grd_outdist)

    ls_steps.append(LABEL_EXPORTING)
    ls_times.append(t)

    # SHUTDOWN
    # -------------------------------------------------------------------
    total_elapsed = time.time() - start_total
    logger.info(format_msg_elapsed(DC_MSG[LABEL_RUN], total_elapsed))
    logger.info(format_msg_output(folder_output))

    # record it in your steps/times lists
    ls_steps.append(LABEL_RUN)
    ls_times.append(total_elapsed)

    # Save all runtime data including total
    runtimes_file = save_runtime_data(
        steps=ls_steps, times=ls_times, folder_output=folder_output
    )
    return True


def analysis_lulc_series(
    folder_output,
    file_lulc_attributes,
    folder_lulc_scenario,
    file_aoi,
    label,
    views,
    talk,
):
    # todo docstring
    from plans.datasets import LULCSeries

    # LOGGING
    # -------------------------------------------------------------------
    tool_name = analysis_lulc_series.__name__
    setup_logger(label=tool_name, talk=talk)

    # DEFINE PROTOCOLS
    # -------------------------------------------------------------------
    @step(LABEL_LOADING)
    def load_inputs():
        #
        lulc_series = LULCSeries(name=label)
        logger.info(f"loading >>> {label} lulc maps ...")
        lulc_series.load_folder(
            folder=folder_lulc_scenario,
            file_table=file_lulc_attributes,
            name_pattern="lulc_*",
            talk=talk,
        )
        # handle basin
        aoi_map = None
        if file_aoi is not None:
            aoi_map = AOI(name=label)
            aoi_map.load_data(file_data=file_aoi)
            lulc_series.apply_aoi_masks(grid_aoi=aoi_map.data, inplace=True)
        return lulc_series, aoi_map

    @step(LABEL_PROCESSING)
    def process_data():
        df = lulc_series.get_series_areas()
        df.rename(columns={"id_raster": "id_lulc_raster"}, inplace=True)
        return df

    @step(LABEL_EXPORTING)
    def export_data(df):
        file_name_output = "lulc_series"
        file_output = Path(folder_output) / f"{file_name_output}.csv"
        logger.info(f"exporting >>> {label} {file_name_output}.csv")
        df.to_csv(file_output, sep=";", index=False)
        if views:
            # format titles
            for k in lulc_series.collection:
                dt = lulc_series.collection[k].datetime
                title = f"{label} | Land Use | {dt}"
                lulc_series.collection[k].view_specs["title"] = title
            # export views
            logger.info(f"exporting >>> {label} lulc map views ...")
            lulc_series.get_views(
                show=False,
                folder=folder_output,
                dpi=300,
                fig_format="jpg",
                talk=False,
                specs=None,
                suffix=None,
            )
        return None

    # START UP
    # -------------------------------------------------------------------
    start_total = time.time()
    ls_steps, ls_times = [], []
    logger.info(LABEL_STARTING)

    # LOADING INPUTS
    # -------------------------------------------------------------------
    (lulc_series, aoi_map), t = load_inputs()

    ls_steps.append(LABEL_LOADING)
    ls_times.append(t)

    # PROCESSING DATA
    # -------------------------------------------------------------------
    df, t = process_data()

    ls_steps.append(LABEL_EXPORTING)
    ls_times.append(t)

    # EXPORTING OUTPUTS
    # -------------------------------------------------------------------
    file_output, t = export_data(df)

    ls_steps.append(LABEL_EXPORTING)
    ls_times.append(t)

    # SHUTDOWN
    # -------------------------------------------------------------------
    total_elapsed = time.time() - start_total
    logger.info(format_msg_elapsed(DC_MSG[LABEL_RUN], total_elapsed))
    logger.info(format_msg_output(folder_output))

    # record it in your steps/times lists
    ls_steps.append(LABEL_RUN)
    ls_times.append(total_elapsed)

    # Save all runtime data including total
    runtimes_file = save_runtime_data(
        steps=ls_steps, times=ls_times, folder_output=folder_output
    )
    return True


def analysis_climate_series_lulc(
    folder_output,
    file_parameters,
    file_climate_series,
    file_lulc_series,
    label,
    views,
    talk,
):
    # todo docstring
    from plans.datasets import RainSeries, ETSeries

    # LOGGING
    # -------------------------------------------------------------------
    tool_name = demo.__name__
    setup_logger(label=tool_name, talk=talk)

    # DEFINE PROTOCOLS
    # -------------------------------------------------------------------
    @step(LABEL_LOADING)
    def load_inputs(file_parameters, file_climate_series, file_lulc_series):

        df_params = pd.read_csv(file_parameters, sep=";")
        dt_value = df_params.loc[df_params["field"] == "dt", "value"].values[
            0
        ]  # Minutes

        ppt = RainSeries()
        ppt.load_data(
            file_data=file_climate_series,
            input_dtfield="datetime",
            input_varfield="ppt",
        )

        pet = ETSeries()
        pet.load_data(
            file_data=file_climate_series,
            input_dtfield="datetime",
            input_varfield="pet",
        )

        df_lulc = pd.read_csv(
            file_lulc_series, sep=";", parse_dates=[TimeSeries().dtfield]
        )
        df_lulc.drop_duplicates(subset="id_lulc_raster", inplace=True)

        return dt_value, ppt, pet, df_lulc

    @step(LABEL_PROCESSING)
    def process_data(dt_value, ppt, pet, df_lulc):
        # downscale
        df_downscaled_ppt = ppt.downscale(freq=f"{dt_value}min")
        df_downscaled_pet = pet.downscale(freq=f"{dt_value}min")
        df_downscaled = pd.merge(
            left=df_downscaled_ppt, right=df_downscaled_pet, on="datetime", how="left"
        )
        df_downscaled["date"] = df_downscaled["datetime"].dt.strftime("%Y-%m-%d")

        # handle lulc
        df_lulc = df_lulc[["datetime", "id_lulc_raster"]].copy()

        df_lulc.rename(columns={"datetime": "date"}, inplace=True)
        df_lulc["date"] = df_lulc["date"].dt.strftime("%Y-%m-%d")

        # merge
        df_downscaled = pd.merge(
            left=df_downscaled, right=df_lulc, on="date", how="left"
        )
        # interpolate voids using nearest method
        df_downscaled["id_lulc_raster"] = df_downscaled["id_lulc_raster"].interpolate(
            method="nearest"
        )
        df_downscaled.drop(columns="date", inplace=True)
        df_downscaled.dropna(subset="id_lulc_raster", inplace=True)
        df_downscaled["id_lulc_raster"] = df_downscaled["id_lulc_raster"].astype(
            dtype="int16"
        )
        df_downscaled.reset_index(drop=True, inplace=True)

        logger.info(
            "processed data:\n\n{}\n\n{}\n\n".format(
                df_downscaled.head(5).to_string(), df_downscaled.tail(5).to_string()
            )
        )

        return df_downscaled

    @step(LABEL_EXPORTING)
    def export_data(df, folder):
        filename = f"climate_series_lulc_{label}.csv"
        file_out = Path(folder) / filename
        logger.info(f"exporting >>> {label} {filename}")
        df.to_csv(file_out, sep=";", index=False)
        return file_out

    # START UP
    # -------------------------------------------------------------------
    start_total = time.time()
    ls_steps, ls_times = [], []
    logger.info(LABEL_STARTING)

    # LOADING INPUTS
    # -------------------------------------------------------------------
    (dt_value, ppt, pet, df_lulc), t = load_inputs(
        file_parameters, file_climate_series, file_lulc_series
    )

    ls_steps.append(LABEL_LOADING)
    ls_times.append(t)

    # PROCESSING DATA
    # -------------------------------------------------------------------
    df_out, t = process_data(dt_value, ppt, pet, df_lulc)

    ls_steps.append(LABEL_PROCESSING)
    ls_times.append(t)

    # EXPORTING OUTPUTS
    # -------------------------------------------------------------------
    file_out, t = export_data(df_out, folder_output)

    ls_steps.append(LABEL_EXPORTING)
    ls_times.append(t)

    # SHUTDOWN
    # -------------------------------------------------------------------
    total_elapsed = time.time() - start_total
    logger.info(format_msg_elapsed(DC_MSG[LABEL_RUN], total_elapsed))
    logger.info(format_msg_output(folder_output))

    # record it in your steps/times lists
    ls_steps.append(LABEL_RUN)
    ls_times.append(total_elapsed)

    # Save all runtime data including total
    runtimes_file = save_runtime_data(
        steps=ls_steps, times=ls_times, folder_output=folder_output
    )
    return True


def analysis_soils_parameters(
    folder_output,
    file_parameters,
    file_soils_attributes,
    file_soils,
    file_basin,
    label,
    views,
    talk,
):
    from plans.datasets import Soils, AOI, SciRaster, RasterCollection
    from plans.geo import downscale_parameter_to_units

    # todo docstring
    # LOGGING
    # -------------------------------------------------------------------
    tool_name = analysis_soils_parameters.__name__
    setup_logger(label=tool_name, talk=talk)

    # DEFINE PROTOCOLS
    # -------------------------------------------------------------------
    @step(LABEL_LOADING)
    def load_inputs():
        # list soil parameters
        # ---------------------------------------------------------------
        logger.info(f"loading >>> {label} parameters table ...")
        df_parameters = parse_spatial_parameters(
            title="Soils Attributes", file_parameters=file_parameters
        )

        # load maps
        # ---------------------------------------------------------------

        logger.info(f"loading >>> {label} soils map ...")
        soils = Soils(name=label)
        soils.load_data(file_data=file_soils, file_table=file_soils_attributes)

        logger.info(f"loading >>> {label} {label} basin map ...")
        basin = AOI(name=label)
        basin.load_data(file_data=file_basin)

        return df_parameters, soils, basin

    @step(LABEL_PROCESSING)
    def process_data():
        # downscaling loop
        # ---------------------------------------------------------------
        parameters = RasterCollection()
        for row in df_values.to_dict(orient="records"):
            upscaled_value = row["value"]
            covar_table = soils.table[["id", row["field"]]].copy()
            covar_table.rename(columns={"id": "v", row["field"]: "w"}, inplace=True)

            # downscale
            # -----------------------------------------------------------
            logger.info(f"processing >>> {label} downscaling {row['name']} ...")
            downscaled_map = downscale_parameter_to_units(
                upscaled_value=row["value"],
                units=soils.data,
                basin=basin.data,
                covariate_table=covar_table,
                mode="mean",
            )

            # set-up
            # -----------------------------------------------------------
            logger.info(f"processing >>> {label} building raster {row['name']} ...")
            parameter = SciRaster(name=row["name"])
            parameter.alias = row["name"]
            parameter.varname = row["name"]
            parameter.varalias = row["name"]
            parameter.units = row["units"]
            parameter.description = row["description"]
            parameter.file_data = f"soils_{row['name']}"

            # inject data
            # -----------------------------------------------------------
            parameter.set_data(grid=downscaled_map)
            parameter.set_raster_metadata(metadata=soils.raster_metadata)
            parameter.get_stats(inplace=True)
            parameter.update()

            # view specs
            # -----------------------------------------------------------
            s_title = f"{label} | {parameter.name} | {parameter.description} {parameter.units}"
            parameter.view_specs["title"] = s_title
            parameter.view_specs["cmap"] = "Oranges"
            parameter.view_specs["ylabel"] = parameter.units
            parameter.view_specs["range"] = [0, 1.1 * parameter.stats["max"]]
            parameter.view_specs["folder"] = folder_output
            parameter.view_specs["filename"] = parameter.file_data

            # append
            # -----------------------------------------------------------
            parameters.append(new_object=parameter)

        return parameters

    @step(LABEL_EXPORTING)
    def export_data():
        export_parameters(
            folder_output=folder_output,
            parameters=parameters,
            basin=basin,
            views=views,
            prefix="soils",
            label=label,
        )
        return True

    # START UP
    # -------------------------------------------------------------------
    start_total = time.time()
    ls_steps, ls_times = [], []
    logger.info(LABEL_STARTING)

    # LOADING INPUTS
    # -------------------------------------------------------------------
    (df_values, soils, basin), t = load_inputs()

    ls_steps.append(LABEL_LOADING)
    ls_times.append(t)

    # PROCESSING DATA
    # -------------------------------------------------------------------
    parameters, t = process_data()

    ls_steps.append(LABEL_PROCESSING)
    ls_times.append(t)

    # EXPORTING OUTPUTS
    # -------------------------------------------------------------------
    out, t = export_data()

    ls_steps.append(LABEL_EXPORTING)
    ls_times.append(t)

    # SHUTDOWN
    # -------------------------------------------------------------------
    total_elapsed = time.time() - start_total
    logger.info(format_msg_elapsed(DC_MSG[LABEL_RUN], total_elapsed))
    logger.info(format_msg_output(folder_output))

    # record it in your steps/times lists
    ls_steps.append(LABEL_RUN)
    ls_times.append(total_elapsed)

    # Save all runtime data including total
    runtimes_file = save_runtime_data(
        steps=ls_steps, times=ls_times, folder_output=folder_output
    )
    return True


def analysis_lulc_parameters(
    folder_output,
    file_parameters,
    file_lulc_attributes,
    folder_lulc_scenario,
    file_basin,
    label,
    views,
    talk,
):
    # todo docstring
    from plans.datasets import LULCSeries, AOI, SciRaster, RasterCollection
    from plans.geo import downscale_parameter_to_units

    # LOGGING
    # -------------------------------------------------------------------
    tool_name = analysis_lulc_parameters.__name__
    setup_logger(label=tool_name, talk=talk)

    # DEFINE PROTOCOLS
    # -------------------------------------------------------------------
    @step(LABEL_LOADING)
    def load_inputs():

        # list lulc parameters
        # ---------------------------------------------------------------
        logger.info(f"loading >>> {label} parameters table ...")
        df_parameters = parse_spatial_parameters(
            title="Land Use Attributes", file_parameters=file_parameters
        )

        # load maps
        # ---------------------------------------------------------------

        logger.info(f"loading >>> {label} lulc maps ...")
        lulc_series = LULCSeries(name=label)
        lulc_series.load_folder(
            folder=folder_lulc_scenario,
            file_table=file_lulc_attributes,
            name_pattern="lulc_*",
            talk=talk,
        )

        logger.info(f"loading >>> {label} basin map ...")
        basin = AOI(name=label)
        basin.load_data(file_data=file_basin)

        return df_parameters, lulc_series, basin

    @step(LABEL_PROCESSING)
    def process_data():
        # downscaling loop
        # ---------------------------------------------------------------
        parameters = RasterCollection()
        for k in lulc_series.collection:
            for row in df_values.to_dict(orient="records"):
                raster_name = f"{k}_{row['name']}"

                upscaled_value = row["value"]
                covar_table = (
                    lulc_series.collection[k].table[["id", row["field"]]].copy()
                )
                covar_table.rename(columns={"id": "v", row["field"]: "w"}, inplace=True)

                # downscale
                # -----------------------------------------------------------
                downscaled_map = downscale_parameter_to_units(
                    upscaled_value=row["value"],
                    units=lulc_series.collection[k].data,
                    basin=basin.data,
                    covariate_table=covar_table,
                    mode="mean",
                )

                # set-up
                # -----------------------------------------------------------
                logger.info(f"processing >>> {label} building raster {raster_name} ...")
                parameter = SciRaster(name=raster_name)
                parameter.alias = row["name"]
                parameter.varname = row["name"]
                parameter.varalias = row["name"]
                parameter.units = row["units"]
                parameter.description = row["description"]

                parameter.file_data = raster_name
                parameter.datetime = lulc_series.collection[k].datetime

                # inject data
                # -----------------------------------------------------------
                parameter.set_data(grid=downscaled_map)
                parameter.set_raster_metadata(
                    metadata=lulc_series.collection[k].raster_metadata
                )
                parameter.get_stats(inplace=True)
                parameter.update()

                # view specs
                # -----------------------------------------------------------
                s_title = f"{label} | {parameter.name} | {parameter.description} {parameter.units}"
                parameter.view_specs["title"] = s_title
                parameter.view_specs["cmap"] = "Oranges"
                parameter.view_specs["ylabel"] = parameter.units
                parameter.view_specs["range"] = [0, 1.1 * parameter.stats["max"]]
                parameter.view_specs["folder"] = folder_output
                parameter.view_specs["filename"] = raster_name

                # append
                # -----------------------------------------------------------
                parameters.append(new_object=parameter)

        return parameters

    @step(LABEL_EXPORTING)
    def export_data():
        export_parameters(
            folder_output=folder_output,
            parameters=parameters,
            basin=basin,
            views=views,
            prefix="lulc",
            label=label,
        )
        return True

    # START UP
    # -------------------------------------------------------------------
    start_total = time.time()
    ls_steps, ls_times = [], []
    logger.info(LABEL_STARTING)

    # LOADING INPUTS
    # -------------------------------------------------------------------
    (df_values, lulc_series, basin), t = load_inputs()

    ls_steps.append(LABEL_LOADING)
    ls_times.append(t)

    # PROCESSING DATA
    # -------------------------------------------------------------------
    parameters, t = process_data()
    print(parameters.catalog)

    ls_steps.append(LABEL_PROCESSING)
    ls_times.append(t)

    # EXPORTING OUTPUTS
    # -------------------------------------------------------------------
    out, t = export_data()

    ls_steps.append(LABEL_EXPORTING)
    ls_times.append(t)

    # SHUTDOWN
    # -------------------------------------------------------------------
    total_elapsed = time.time() - start_total
    logger.info(format_msg_elapsed(DC_MSG[LABEL_RUN], total_elapsed))
    logger.info(format_msg_output(folder_output))

    # record it in your steps/times lists
    ls_steps.append(LABEL_RUN)
    ls_times.append(total_elapsed)

    # Save all runtime data including total
    runtimes_file = save_runtime_data(
        steps=ls_steps, times=ls_times, folder_output=folder_output
    )
    return True


def func2(path: str, flag: bool):
    print(f"func2 running: path={path}, flag={flag}")


# ... {develop}

# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


def main():

    def add_arguments_str(parser, arguments):
        parser.add_argument(
            "--{}".format(arguments["flag"]),
            required=arguments["required"],
            help=arguments["help"],
            default=arguments["default"],
        )
        return parser

    def add_arguments_bool(parser, arguments):
        parser.add_argument("--{}".format(arguments["flag"]), action="store_true")
        return parser

    def add_arguments(parser, arguments):
        for a in arguments:
            if a["type"] == "str":
                parser = add_arguments_str(parser, arguments=a)
            elif a["type"] == "bool":
                parser = add_arguments_bool(parser, arguments=a)
        return parser

    # LISTED PARSERS
    # ===================================================================
    parser = argparse.ArgumentParser(description="Tools runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # demo
    # -------------------------------------------------------------------
    dc_args = [
        {
            "type": "str",
            "flag": "folder",
            "required": True,
            "default": None,
            "help": "output folder file path",
        },
        {
            "type": "str",
            "flag": "input1",
            "required": True,
            "default": None,
            "help": "input 1 file path",
        },
        {
            "type": "str",
            "flag": "input2",
            "required": True,
            "default": None,
            "help": "input 2 file path",
        },
        {
            "type": "bool",
            "flag": "talk",
            "action": "store_true",
        },
    ]
    parser_demo = subparsers.add_parser("demo", help="Run demo()")
    parser_demo = add_arguments(parser_demo, dc_args)

    # dto
    # -------------------------------------------------------------------
    dc_args = [
        {
            "type": "str",
            "flag": "folder",
            "required": True,
            "default": None,
            "help": "output folder file path",
        },
        {
            "type": "str",
            "flag": "ldd",
            "required": True,
            "default": None,
            "help": "path to ldd.tif map",
        },
        {
            "type": "str",
            "flag": "basin",
            "required": False,
            "default": None,
            "help": "path to basin.tif map",
        },
        {
            "type": "str",
            "flag": "label",
            "required": True,
            "default": LABEL_PROJECT,
            "help": "project label",
        },
        {
            "type": "bool",
            "flag": "views",
            "action": "store_true",
        },
        {
            "type": "bool",
            "flag": "talk",
            "action": "store_true",
        },
    ]
    parser_dto = subparsers.add_parser("analysis_dto", help="Run dto()")
    parser_dto = add_arguments(parser_dto, dc_args)

    # lulc_series
    # -------------------------------------------------------------------
    dc_args = [
        {
            "type": "str",
            "flag": "folder",
            "required": True,
            "default": None,
            "help": "output folder file path",
        },
        {
            "type": "str",
            "flag": "attributes",
            "required": True,
            "default": None,
            "help": "path to lulc attribute table",
        },
        {
            "type": "str",
            "flag": "scenario",
            "required": True,
            "default": None,
            "help": "path to folder with lulc scenario maps",
        },
        {
            "type": "str",
            "flag": "aoi",
            "required": False,
            "default": None,
            "help": "path to aoi or basin map",
        },
        {
            "type": "str",
            "flag": "label",
            "required": True,
            "default": LABEL_PROJECT,
            "help": "project label",
        },
        {
            "type": "bool",
            "flag": "views",
            "action": "store_true",
        },
        {
            "type": "bool",
            "flag": "talk",
            "action": "store_true",
        },
    ]
    parser_lulc_series = subparsers.add_parser("analysis_lulc_series", help="Run dto()")
    parser_lulc_series = add_arguments(parser_lulc_series, dc_args)

    # climate_lulc_series
    # -------------------------------------------------------------------
    dc_args = [
        {
            "type": "str",
            "flag": "folder",
            "required": True,
            "default": None,
            "help": "output folder file path",
        },
        {
            "type": "str",
            "flag": "parameters",
            "required": True,
            "default": None,
            "help": "path to parameters table",
        },
        {
            "type": "str",
            "flag": "climate",
            "required": True,
            "default": None,
            "help": "path to climate series",
        },
        {
            "type": "str",
            "flag": "lulc",
            "required": False,
            "default": None,
            "help": "path to lulc series",
        },
        {
            "type": "str",
            "flag": "label",
            "required": True,
            "default": LABEL_PROJECT,
            "help": "project label",
        },
        {
            "type": "bool",
            "flag": "views",
            "action": "store_true",
        },
        {
            "type": "bool",
            "flag": "talk",
            "action": "store_true",
        },
    ]
    parser_climate_lulc_series = subparsers.add_parser(
        "analysis_climate_series_lulc", help="Run "
    )
    parser_climate_lulc_series = add_arguments(parser_climate_lulc_series, dc_args)

    # soils parameters
    # -------------------------------------------------------------------
    dc_args = [
        {
            "type": "str",
            "flag": "folder",
            "required": True,
            "default": None,
            "help": "output folder file path",
        },
        {
            "type": "str",
            "flag": "parameters",
            "required": True,
            "default": None,
            "help": "path to parameters table",
        },
        {
            "type": "str",
            "flag": "attributes",
            "required": True,
            "default": None,
            "help": "path to soils attributes table",
        },
        {
            "type": "str",
            "flag": "soils",
            "required": False,
            "default": None,
            "help": "path to soils map",
        },
        {
            "type": "str",
            "flag": "basin",
            "required": False,
            "default": None,
            "help": "path to basin map",
        },
        {
            "type": "str",
            "flag": "label",
            "required": True,
            "default": LABEL_PROJECT,
            "help": "project label",
        },
        {
            "type": "bool",
            "flag": "views",
            "action": "store_true",
        },
        {
            "type": "bool",
            "flag": "talk",
            "action": "store_true",
        },
    ]
    ps_soils_parameters = subparsers.add_parser(
        "analysis_soils_parameters", help="Run "
    )
    ps_soils_parameters = add_arguments(ps_soils_parameters, dc_args)

    # lulc parameters
    # -------------------------------------------------------------------
    dc_args = [
        {
            "type": "str",
            "flag": "folder",
            "required": True,
            "default": None,
            "help": "output folder file path",
        },
        {
            "type": "str",
            "flag": "parameters",
            "required": True,
            "default": None,
            "help": "path to parameters table",
        },
        {
            "type": "str",
            "flag": "attributes",
            "required": True,
            "default": None,
            "help": "path to lulc attributes table",
        },
        {
            "type": "str",
            "flag": "scenario",
            "required": True,
            "default": None,
            "help": "path to folder with lulc scenario maps",
        },
        {
            "type": "str",
            "flag": "basin",
            "required": False,
            "default": None,
            "help": "path to basin map",
        },
        {
            "type": "str",
            "flag": "label",
            "required": True,
            "default": LABEL_PROJECT,
            "help": "project label",
        },
        {
            "type": "bool",
            "flag": "views",
            "action": "store_true",
        },
        {
            "type": "bool",
            "flag": "talk",
            "action": "store_true",
        },
    ]
    ps_lulc_parameters = subparsers.add_parser("analysis_lulc_parameters", help="Run ")
    ps_lulc_parameters = add_arguments(ps_lulc_parameters, dc_args)

    # commands
    # -------------------------------------------------------------------
    args = parser.parse_args()

    if args.command == "demo":
        demo(args.folder, args.input1, args.input2, args.talk)
    elif args.command == "analysis_dto":
        analysis_dto(
            args.folder, args.ldd, args.basin, args.label, args.views, args.talk
        )
    elif args.command == "analysis_lulc_series":
        analysis_lulc_series(
            args.folder,
            args.attributes,
            args.scenario,
            args.aoi,
            args.label,
            args.views,
            args.talk,
        )
    elif args.command == "analysis_climate_series_lulc":
        analysis_climate_series_lulc(
            args.folder,
            args.parameters,
            args.climate,
            args.lulc,
            args.label,
            args.views,
            args.talk,
        )
    elif args.command == "analysis_soils_parameters":
        analysis_soils_parameters(
            args.folder,
            args.parameters,
            args.attributes,
            args.soils,
            args.basin,
            args.label,
            args.views,
            args.talk,
        )
    elif args.command == "analysis_lulc_parameters":
        analysis_lulc_parameters(
            args.folder,
            args.parameters,
            args.attributes,
            args.scenario,
            args.basin,
            args.label,
            args.views,
            args.talk,
        )


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Call main
    # ===================================================================
    main()
