# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Input-output processing routines.


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
    print("Hello World!")

Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl. Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl.

"""

import glob
import logging
import multiprocessing
import os, time, shutil
import numpy as np
from plans.cli import logger_setup
import plans.hydrology as hydro
import plans.datasets.spatial as sp


# ------------------------------ UTILS ------------------------------
# docs ok
def nowsep(sep="-"):
    """Generate a timestamp string with the current date and time separated by the specified separator.

    :param sep: str, optional
        Separator to use between date and time components, default is '-'.
    :type sep: str

    :return: str
        Timestamp string formatted as 'YYYY-MM-DD-HH-MM-SS'.
    :rtype: str

    **Notes:**

    - Uses the current date and time to generate a timestamp string.
    - The default separator is '-'.

    """
    import datetime

    def_now = datetime.datetime.now()
    yr = def_now.strftime("%Y")
    mth = def_now.strftime("%m0")
    dy = def_now.strftime("%d")
    hr = def_now.strftime("%H")
    mn = def_now.strftime("%M")
    sg = def_now.strftime("%S")
    def_lst = [yr, mth, dy, hr, mn, sg]
    def_s = str(sep.join(def_lst))
    return def_s


# docs ok
def create_rundir(workplace, run_id, prefix=None, suffix=None, b_time=True):
    """Create a directory for a run with an optional label, suffix, and timestamp."""
    # define labels
    if prefix is None:
        prefix = ""
    else:
        prefix = prefix + "_"

    if suffix is None:
        suffix = ""
    else:
        suffix = "_" + suffix

    # define dir path
    dir_path = workplace + "/" + f"{prefix}{run_id}{suffix}"
    # include time stamp
    if b_time:
        dir_path = dir_path + "_" + nowsep()
    # make
    if os.path.isdir(dir_path):
        pass
    else:
        os.mkdir(dir_path)
    return dir_path


# ------------------------------ UTILS - DRY TOOLS ------------------------------


def _get_dict_basins(folder_basins):
    m_basins = sp.Basins(name="Basins")
    m_basins.load_data(
        asc_file=os.path.join(folder_basins, "basins.asc"),
        prj_file=os.path.join(folder_basins, "basins.prj"),
        table_file=os.path.join(folder_basins, "basins_info.csv"),
    )
    basins_dct = {}
    for i in range(len(m_basins.table)):
        basins_id = m_basins.table["Id"].values[i]
        basins_dct[basins_id] = m_basins.get_basin_aoi(basin_id=basins_id)

    return basins_dct


# ------------------------------ TOOLS ------------------------------


# todo develop a proper object (class) for tools and also handle serial and multiprocessing
def DEMO(
    project_name,
    inputfile1,
    folder_output,
    b_param1,
    workplace=True,
    talk=False,
    export_inputs=False,
    export_views=False,
    sleep=False,
    sleep_secs=1,
):
    # ---------------------- START ----------------------
    start_start = time.time()
    # define label
    toolname = DEMO.__name__
    prompt = "{}@{}: [{}]".format("plans", project_name, toolname)

    # ---------------------- RUN DIR ----------------------
    if workplace:
        folder_output = create_rundir(
            workplace=folder_output, label=project_name, suffix=toolname
        )

    # ---------------------- LOGGER ----------------------
    logger = logger_setup(
        logger_name=toolname,
        streamhandler=talk,
        filehandler=True,
        logfile="{}/logs.log".format(folder_output),
    )
    logger.info("{} start".format(prompt))
    logger.info("{} run folder at {}".format(prompt, folder_output))

    # ---------------------- LOAD ----------------------
    s_step = "loading"
    logger.info("{} {} data ...".format(prompt, s_step))
    start_time = time.time()

    if sleep:
        time.sleep(sleep_secs)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(
        "{} {} elapsed time: {} seconds".format(prompt, s_step, round(elapsed_time, 3))
    )

    # ---------------------- PROCESSING ----------------------
    s_step = "processing"
    logger.info("{} {} data ...".format(prompt, s_step))
    start_time = time.time()

    if sleep:
        time.sleep(sleep_secs)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(
        "{} {} elapsed time: {} seconds".format(prompt, s_step, round(elapsed_time, 3))
    )

    # ---------------------- EXPORTING - INPUTS ----------------------
    if export_inputs:
        s_step = "exporting inputs"
        logger.info("{} {} data ...".format(prompt, s_step))
        start_time = time.time()

        # make dir
        inpdir = "{}/inputs".format(folder_output)
        os.mkdir(path=inpdir)

        # copy files or export
        if sleep:
            time.sleep(sleep_secs)

        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(
            "{} {} elapsed time: {} seconds".format(
                prompt, s_step, round(elapsed_time, 3)
            )
        )

    # ---------------------- EXPORTING - OUTPUTS ----------------------
    s_step = "exporting output"
    logger.info("{} {} data ...".format(prompt, s_step))
    start_time = time.time()

    if sleep:
        time.sleep(sleep_secs)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(
        "{} {} elapsed time: {} seconds".format(prompt, s_step, round(elapsed_time, 3))
    )

    # ---------------------- END ----------------------
    end_end = time.time()
    elapsed_time = end_end - start_start
    logger.info("{} end".format(prompt))
    logger.info(
        "{} total elapsed time: {} seconds".format(prompt, round(elapsed_time, 3))
    )
    return 0


def MLS(
    run_id,
    bootfile,
    folder_output,
    workplace=True,
    talk=False,
    export_inputs=False,
    export_views=False,
    sleep=False,
    sleep_secs=1,
):
    # ---------------------- START ----------------------
    start_start = time.time()
    # define label
    toolname = MLS.__name__
    prompt = "{}@{}: [{}]".format("plans", run_id, toolname)

    # ---------------------- RUN DIR ----------------------
    if workplace:
        folder_output = create_rundir(
            workplace=folder_output, run_id=run_id, prefix="LS", suffix=toolname
        )

    # ---------------------- LOAD ----------------------
    m = hydro.LinearStorage(name=run_id, alias=run_id)
    m.boot(bootfile=bootfile)
    m.load()

    if sleep:
        time.sleep(sleep_secs)

    # ---------------------- PROCESSING ----------------------
    m.run()
    m.evaluate()
    if sleep:
        time.sleep(sleep_secs)

    # ---------------------- EXPORTING - INPUTS ----------------------
    if export_inputs:
        # make dir
        inpdir = "{}/inputs".format(folder_output)
        os.mkdir(path=inpdir)
        # copy files or export
        # develop logic
        if sleep:
            time.sleep(sleep_secs)

    # ---------------------- EXPORTING - OUTPUTS ----------------------
    m.export(folder=folder_output, filename=m.name, views=export_views)

    if sleep:
        time.sleep(sleep_secs)

    # ---------------------- END ----------------------

    return 0


def _run_mls_task(args):
    """Função auxiliar para encapsular a chamada MLS com múltiplos argumentos,
    permitindo que ela seja usada com pool.map().

    :param args: Uma tupla contendo todos os argumentos necessários para MLS.
    :type args: tuple
    :return: O resultado da função MLS.
    :rtype: int
    """
    (
        run_id,
        bootfile,
        folder_output,
        talk,
        workplace,
        export_inputs,
        export_views,
        sleep,
        sleep_secs,
    ) = args
    return MLS(
        run_id=run_id,
        bootfile=bootfile,
        folder_output=folder_output,
        workplace=workplace,
        talk=talk,
        export_inputs=export_inputs,
        export_views=export_views,
        sleep=sleep,
        sleep_secs=sleep_secs,
    )


def MLS_bat(
    folder_bootfiles,
    project_name,
    folder_output,
    bat_type="serial",
    talk=False,
    workplace=True,
    export_inputs=False,
    export_views=False,
    sleep=False,
    sleep_secs=2,
    num_processes=None,
):
    start_start = time.time()

    # get bootfiles
    ls_bootfiles = glob.glob(f"{folder_bootfiles}/*.csv")

    if bat_type == "parallel":
        # todo refactor IA code bellow
        print(f"Iniciando processamento paralelo para {len(ls_bootfiles)} arquivos...")

        # Prepara a lista de argumentos para cada chamada MLS
        # Cada item na lista será uma tupla de argumentos para _run_mls_task
        task_args = [
            (
                os.path.basename(bootfile).split(".")[0],
                bootfile,
                folder_output,
                talk,
                workplace,
                export_inputs,
                export_views,
                sleep,
                sleep_secs,
            )
            for bootfile in ls_bootfiles
        ]
        # Define o número de processos a serem usados
        processes_to_use = (
            num_processes if num_processes is not None else multiprocessing.cpu_count()
        )
        print(f"Utilizando {processes_to_use} processos.")

        with multiprocessing.Pool(processes=processes_to_use) as pool:
            # pool.map aplica a função _run_mls_task a cada tupla em task_args
            # Os resultados serão retornados na mesma ordem em que as tarefas foram enviadas
            results = pool.map(_run_mls_task, task_args)

        print("Processamento paralelo concluído.")
        # Você pode inspecionar 'results' se precisar dos retornos de cada chamada MLS
        # print("Resultados individuais:", results)

    else:  # defaults to serial processing
        # serial loop
        for i in range(len(ls_bootfiles)):
            bootfile = ls_bootfiles[i]
            print(bootfile)
            n_result = MLS(
                run_id=os.path.basename(bootfile).split(".")[0],
                bootfile=bootfile,
                folder_output=folder_output,
                workplace=True,
                talk=talk,
                export_inputs=export_inputs,
                export_views=export_views,
                sleep=sleep,
                sleep_secs=sleep_secs,
            )

    end_time = time.time()
    elapsed_time = end_time - start_start
    print("total elapsed time: {} seconds".format(round(elapsed_time, 3)))
    return 0


def VTOPO(
    project_name,
    datasets_dir,
    outdir,
    by_basins=True,
    workplace=True,
    talk=False,
):
    # todo [docstring]

    # ---------------------- START ----------------------
    start_start = time.time()
    # define label
    toolname = VTOPO.__name__
    prompt = "{}@{}: [{}]".format("plans", project_name, toolname)

    # ---------------------- RUN DIR ----------------------
    if workplace:
        outdir = create_rundir(workplace=outdir, label=toolname, suffix=project_name)

    # ---------------------- LOGGER ----------------------
    logger = logger_setup(
        logger_name=toolname,
        streamhandler=talk,
        filehandler=True,
        logfile="{}/logs.log".format(outdir),
    )
    logger.info("{} start".format(prompt))
    logger.info("{} run folder at {}".format(prompt, outdir))

    # ---------------------- LOAD ----------------------
    s_step = "loading"
    logger.info("{} {} data ...".format(prompt, s_step))
    start_time = time.time()

    # folder setup
    folder_topo = os.path.join(datasets_dir, "topo")
    folder_basins = os.path.join(datasets_dir, "basins")

    # get basins aois
    if by_basins:
        basins_dct = _get_dict_basins(folder_basins=folder_basins)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(
        "{} {} elapsed time: {} seconds".format(prompt, s_step, round(elapsed_time, 3))
    )

    # ---------------------- PROCESSING ----------------------
    s_step = "processing"
    logger.info("{} {} data ...".format(prompt, s_step))
    start_time = time.time()

    # dem
    dct_topo = {
        "dem": sp.Elevation,
        "twi": sp.TWI,
        "hand": sp.HAND,
        "slope": sp.Slope,
        "ldd": sp.LDD,
        "accflux": sp.FAC,
    }

    # full folder setup
    folder_full = outdir
    if by_basins:
        folder_full = os.path.join(outdir, "full")
        if not os.path.isdir(folder_full):
            os.mkdir(folder_full)

    for topo in dct_topo:
        logger.info("{} {:<12} {:<10} -- full ...".format(prompt, "processing", topo))
        m = dct_topo[topo](name=project_name)
        m.load_data(
            asc_file=os.path.join(folder_topo, "{}.asc".format(topo)),
            prj_file=os.path.join(folder_topo, "{}.prj".format(topo)),
        )
        # run main view
        logger.info("{} {:<12} {:<10} -- full ...".format(prompt, "exporting", topo))

        _filename = topo
        if by_basins:
            _filename = "{}-full".format(topo)
        m.view(show=False, folder=folder_full, filename=_filename)

        # run basins loop
        if by_basins:
            for b in basins_dct:
                # basin folder setup
                folder_basin = os.path.join(outdir, "basin_{}".format(b))
                if not os.path.isdir(folder_basin):
                    os.mkdir(folder_basin)

                logger.info(
                    "{} {:<12} {:<10} -- basin_{} ...".format(
                        prompt, "processing", topo, b
                    )
                )
                m.apply_aoi_mask(grid_aoi=basins_dct[b].data)

                # run sub views
                logger.info(
                    "{} {:<12} {:<10} -- basin_{} ...".format(
                        prompt, "exporting", topo, b
                    )
                )
                m.view(
                    show=False,
                    folder=folder_basin,
                    filename="{}-basin_{}".format(topo, b),
                )
                m.release_aoi_mask()

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(
        "{} {} elapsed time: {} seconds".format(prompt, s_step, round(elapsed_time, 3))
    )

    # ---------------------- END ----------------------
    end_end = time.time()
    elapsed_time = end_end - start_start
    logger.info("{} end".format(prompt))
    logger.info(
        "{} total elapsed time: {} seconds".format(prompt, round(elapsed_time, 3))
    )
    return 0


def VLULC(
    project_name,
    datasets_dir,
    outdir,
    scenario="obs",
    by_basins=True,
    workplace=True,
    talk=False,
):
    # todo [docstring]

    # ---------------------- START ----------------------
    start_start = time.time()
    # define label
    toolname = VLULC.__name__
    prompt = "{}@{}: [{}]".format("plans", project_name, toolname)

    # ---------------------- RUN DIR ----------------------
    if workplace:
        outdir = create_rundir(workplace=outdir, label=toolname, suffix=project_name)

    # ---------------------- LOGGER ----------------------
    logger = logger_setup(
        logger_name=toolname,
        streamhandler=talk,
        filehandler=True,
        logfile="{}/logs.log".format(outdir),
    )
    logger.info("{} start".format(prompt))
    logger.info("{} run folder at {}".format(prompt, outdir))

    # ---------------------- LOAD ----------------------
    s_step = "loading"
    logger.info("{} {} data ...".format(prompt, s_step))
    start_time = time.time()

    # folder setup
    folder_lulc = os.path.join(datasets_dir, "lulc")
    folder_lulc = os.path.join(folder_lulc, scenario)
    folder_basins = os.path.join(datasets_dir, "basins")

    # get basins aois
    if by_basins:
        basins_dct = _get_dict_basins(folder_basins=folder_basins)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(
        "{} {} elapsed time: {} seconds".format(prompt, s_step, round(elapsed_time, 3))
    )

    # ---------------------- PROCESSING ----------------------
    s_step = "processing"
    logger.info("{} {} data ...".format(prompt, s_step))
    start_time = time.time()

    # full folder setup
    folder_full = outdir
    if by_basins:
        folder_full = os.path.join(outdir, "full")
        if not os.path.isdir(folder_full):
            os.mkdir(folder_full)

    lulc_series = sp.LULCSeries(name=project_name)
    logger.info("{} loading LULC series ...".format(prompt))
    lulc_series.load_folder(
        folder=folder_lulc,
        file_table=os.path.join(folder_lulc, "lulc_info.csv"),
        name_pattern="lulc_*",
        talk=False,
        use_parallel=False,
    )
    logger.info("{} exporting LULC series ...".format(prompt))
    lulc_series.get_views(show=False, export_areas=False, folder=folder_full)
    logger.info("{} exporting LULC areas ...".format(prompt))
    lulc_series.view_series_areas(
        show=False, export_areas=True, folder=folder_full, filename="lulc_areas"
    )

    # proceed by basins
    if by_basins:
        for b in basins_dct:
            folder_basin = os.path.join(outdir, "basin_{}".format(b))
            if not os.path.isdir(folder_basin):
                os.mkdir(folder_basin)

            logger.info("{} {:<12} -- basin_{} ...".format(prompt, "processing", b))
            lulc_series.apply_aoi_masks(grid_aoi=basins_dct[b].data)
            # run sub views
            logger.info(
                "{} {:<12} -- basin_{} ...".format(prompt, "exporting views", b)
            )
            # views
            lulc_series.get_views(show=False, export_areas=False, folder=folder_basin)
            logger.info(
                "{} {:<12} -- basin_{} ...".format(prompt, "exporting areas", b)
            )
            # areas
            lulc_series.view_series_areas(
                show=False,
                export_areas=True,
                folder=folder_basin,
                filename="lulc_areas_{}".format(b),
            )
            lulc_series.release_aoi_masks()

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(
        "{} {} elapsed time: {} seconds".format(prompt, s_step, round(elapsed_time, 3))
    )

    # ---------------------- END ----------------------
    end_end = time.time()
    elapsed_time = end_end - start_start
    logger.info("{} end".format(prompt))
    logger.info(
        "{} total elapsed time: {} seconds".format(prompt, round(elapsed_time, 3))
    )
    return 0


def TSC(
    kind,
    project_name,
    file_infotable,
    outdir,
    workplace=True,
    talk=False,
    clear_outliers=True,
    datarange_min=None,
    datarange_max=None,
    regionalize=False,
    export_inputs=False,
    export_views=False,
    filter_date_start=None,
    filter_date_end=None,
):
    """Process and analyze ``TSC`` (time series collection) data.

    **Notes:**

    - Performs data loading, processing, and exporting based on specified parameters.
    - Handles various types of time series data, such as rain, stage, and temperature.
    - Supports options for outlier cleaning, regionalization, and exporting inputs and views.

    **Examples:**

    .. code-block:: python

        from plans import tools

        tools.TSC(
            kind="rain",
            run_id="myproject",
            file_infotable="path/to/infotable.csv",
            folder_output="path/to/output",
            workplace=True,
            talk=True,
            clear_outliers=True,
            datarange_min=0,
            datarange_max=120,
            regionalize=False
            export_inputs=True,
            export_views=True,
            filter_date_start="2018-01-01 00:00:00",
            filter_date_end="2023-01-01 00:00:00"
        )


    :param kind: str
        Type of time series data ('rain', 'stage', 'temperature', etc.).
    :type kind: str

    :param project_name: str
        Name of the project.
    :type project_name: str

    :param file_infotable: str
        Path to the information table file.
    :type file_infotable: str

    :param outdir: str
        Output directory where results will be saved.
    :type outdir: str

    :param workplace: bool, optional
        If True, create a run directory in the provided 'folder_output', default is True.
    :type workplace: bool

    :param talk: bool, optional
        If True, enable streamhandler for logging output, default is False.
    :type talk: bool

    :param clear_outliers: bool, optional
        If True, clean outliers in the time series data, default is True.
    :type clear_outliers: bool

    :param datarange_min: datetime or None, optional
        Minimum date range for filtering data, default is None.
    :type datarange_min: datetime or None

    :param datarange_max: datetime or None, optional
        Maximum date range for filtering data, default is None.
    :type datarange_max: datetime or None

    :param regionalize: bool, optional
        If True, perform regionalization, default is False.
    :type regionalize: bool

    :param export_inputs: bool, optional
        If True, export inputs data, default is False.
    :type export_inputs: bool

    :param export_views: bool, optional
        If True, export views and visualizations, default is False.
    :type export_views: bool

    :param filter_date_start: datetime or None, optional
        Start date for filtering data, default is None.
    :type filter_date_start: datetime or None

    :param filter_date_end: datetime or None, optional
        End date for filtering data, default is None.
    :type filter_date_end: datetime or None

    :return: int
        Returns 0 upon successful completion.
    :rtype: int



    """
    from plans import datasets
    from plans.geo import distance_to_outlet

    # ---------------------- START ----------------------
    start_start = time.time()

    # define label
    if regionalize:
        level = 2
    else:
        level = 1

    toolname = TSC.__name__ + "_T{}_".format(level) + kind
    prompt = "{}@{}: [{}]".format("plans", project_name, toolname)

    # ---------------------- RUN DIR ----------------------
    if workplace:
        outdir = create_rundir(workplace=outdir, label=toolname, suffix=project_name)

    # ---------------------- LOGGER ----------------------
    logger = logger_setup(
        logger_name=toolname,
        streamhandler=talk,
        filehandler=True,
        logfile="{}/logs.log".format(outdir),
    )
    logger.info("{} start".format(prompt))
    logger.info("{} run folder at {}".format(prompt, outdir))

    # ---------------------- LOAD ----------------------
    s_step = "loading"
    logger.info("{} {} ...".format(prompt, s_step))
    start_time = time.time()

    # Naming Setup
    if kind == "rain":
        tsc = datasets.RainSeriesSamples(name=kind + "_" + project_name)
        method = "idw"
    elif kind == "stage":
        tsc = datasets.StageSeriesCollection(name=kind + "_" + project_name)
    elif kind == "temperature":
        tsc = datasets.StageSeriesCollection(name=kind + "_" + project_name)
        method = "average"
    else:
        tsc = datasets.RainSeriesSamples(name=kind + "_" + project_name)
        method = "idw"

    # load from info table
    tsc.load_data(
        table_file=file_infotable, filter_dates=[filter_date_start, filter_date_end]
    )
    tsc.datarange_min = datarange_min
    tsc.datarange_max = datarange_max

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(
        "{} {} --- elapsed time: {} seconds".format(
            prompt, s_step, round(elapsed_time, 3)
        )
    )

    # ---------------------- PROCESSING ----------------------
    s_step = "processing"
    logger.info("{} {} ...".format(prompt, s_step))
    start_time = time.time()

    if clear_outliers:
        logger.info("{} {} --- clean outliers".format(prompt, s_step))
        tsc.clear_outliers()

    logger.info("{} {} --- standardize".format(prompt, s_step))
    tsc.standardize()

    if regionalize:
        logger.info("{} {} --- regionalize".format(prompt, s_step))
        tsc.regionalize(method=method)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(
        "{} {} --- elapsed time: {} seconds".format(
            prompt, s_step, round(elapsed_time, 3)
        )
    )

    # ---------------------- EXPORTING - INPUTS ----------------------
    if export_inputs:
        s_step = "exporting inputs"
        logger.info("{} {} ...".format(prompt, s_step))
        start_time = time.time()

        # make dir
        inpdir = "{}/inputs".format(outdir)
        os.mkdir(path=inpdir)
        logger.info("{} {} --- inputs folder at ./inputs".format(prompt, s_step))

        # export inputs main data
        logger.info("{} {} --- info table".format(prompt, s_step))
        # copy info table
        src = file_infotable
        shutil.copy(src=src, dst="{}/{}".format(inpdir, os.path.basename(src)))

        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(
            "{} {} --- elapsed time: {} seconds".format(
                prompt, s_step, round(elapsed_time, 3)
            )
        )

    # ---------------------- EXPORTING - OUTPUTS ----------------------
    s_step = "exporting output"
    logger.info("{} {} ...".format(prompt, s_step))
    start_time = time.time()

    # export main data
    logger.info("{} {} --- time series collection".format(prompt, s_step))
    # export the catalog
    df = tsc.catalog
    df["VarField"] = df["VarField"] + "_" + df["Alias"]
    df["File"] = "{}/{}.csv".format(outdir, tsc.name)
    df.to_csv("{}/{}_info.csv".format(outdir, tsc.name), sep=";", index=False)
    # export merged data
    tsc.export_data(folder=outdir, merged=True)

    if export_views:
        # export view
        logger.info("{} {} --- exporting views".format(prompt, s_step))
        # only raw
        tsc.export_views(folder=outdir, skip_main=True, raw=True)
        # epochs
        tsc.export_views(folder=outdir, skip_main=False, raw=False)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(
        "{} {} --- elapsed time: {} seconds".format(
            prompt, s_step, round(elapsed_time, 3)
        )
    )

    # ---------------------- END ----------------------
    end_end = time.time()
    elapsed_time = end_end - start_start
    logger.info(
        "{} total elapsed time: {} seconds".format(prompt, round(elapsed_time, 3))
    )
    logger.info("{} end".format(prompt))
    return 0


# docs ok
def DTO(
    project_name,
    file_ldd,
    outdir,
    workplace=True,
    talk=False,
    export_inputs=False,
    export_views=False,
):
    """
    Generate ``DTO`` (Distance To Outlet) raster map using a given ``LDD`` (Local Drain Direction) map.

    :param project_name: Name of the project.
    :type project_name: str
    :param file_ldd: Path to the ``LDD`` (Local Drain Direction) raster file.
    :type file_ldd: str
    :param outdir: Output directory where results will be saved.
    :type outdir: str
    :param workplace: If True, create a run directory in the provided 'folder_output', default is True.
    :type workplace: bool

    :param talk: If True, enable streamhandler for logging output, default is False.
    :type talk: bool

    :param export_inputs: If True, export inputs data, default is False.
    :type export_inputs: bool

    :param export_views: If True, export views and visualizations, default is False.
    :type export_views: bool

    :return: Returns 0 upon successful completion.
    :rtype: int

    **Notes**

    - Generates a Distance to Outlet (``DTO``) raster map from Local Drain Direction (``LDD``).
    - Calculates the hydrological distance from each grid cell to the nearest outlet.
    - Supports export of inputs ``LDD`` map, ``LDD`` views, DTO map, and DTO views.


    **Examples**


    .. code-block:: python

        from plans import tools

        tools.DTO(
            run_id='MyProject',
            file_ldd='path/to/ldd.asc',
            folder_output='output_directory',
            workplace=True,
            talk=False,
            export_inputs=True,
            export_views=True,
        )


    """
    from plans.datasets import Raster, LDD, DTO
    from plans.geo import distance_to_outlet

    # ---------------------- START ----------------------
    start_start = time.time()
    # define label
    toolname = DTO.__name__
    prompt = "{}@{}: [{}]".format("plans", project_name, toolname)

    # ---------------------- RUN DIR ----------------------
    if workplace:
        outdir = create_rundir(workplace=outdir, label=toolname, suffix=project_name)

    # ---------------------- LOGGER ----------------------
    logger = logger_setup(
        logger_name=toolname,
        streamhandler=talk,
        filehandler=True,
        logfile="{}/logs.log".format(outdir),
    )
    logger.info("{} start".format(prompt))
    logger.info("{} run folder at {}".format(prompt, outdir))

    # ---------------------- LOAD ----------------------
    s_step = "loading"
    logger.info("{} {} ...".format(prompt, s_step))
    start_time = time.time()

    ldd = LDD(name=project_name)
    ldd.load_data(asc_file=file_ldd)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(
        "{} {} --- elapsed time: {} seconds".format(
            prompt, s_step, round(elapsed_time, 3)
        )
    )

    # ---------------------- PROCESSING ----------------------
    s_step = "processing"
    logger.info("{} {} ...".format(prompt, s_step))
    start_time = time.time()

    grd_outdist = distance_to_outlet(grd_ldd=ldd.data, n_res=ldd.cellsize, b_tui=talk)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(
        "{} {} --- elapsed time: {} seconds".format(
            prompt, s_step, round(elapsed_time, 3)
        )
    )

    # ---------------------- EXPORTING - INPUTS ----------------------
    if export_inputs:
        s_step = "exporting inputs"
        logger.info("{} {} data ...".format(prompt, s_step))
        start_time = time.time()

        # make dir
        inpdir = "{}/inputs".format(outdir)
        os.mkdir(path=inpdir)
        logger.info("{} inputs folder at {}".format(prompt, inpdir))

        filename = "ldd_{}".format(project_name)

        # export map
        logger.info("{} exporting LDD raster map".format(prompt, inpdir))
        ldd.export(folder=inpdir, filename=filename)
        if export_views:
            # export view
            logger.info("{} exporting LDD raster view".format(prompt, inpdir))
            ldd.view(show=False, filename=filename, folder=inpdir)

        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(
            "{} {} --- elapsed time: {} seconds".format(
                prompt, s_step, round(elapsed_time, 3)
            )
        )

    # ---------------------- EXPORTING - OUTPUTS ----------------------
    s_step = "exporting output"
    logger.info("{} {} ...".format(prompt, s_step))
    start_time = time.time()

    dto = DTO(name=project_name)
    # set metadata
    logger.info("{} {} --- DTO setup".format(prompt, s_step))
    _asc_metadata = ldd.raster_metadata.copy()
    _asc_metadata["NODATA_value"] = -1
    dto.set_raster_metadata(metadata=_asc_metadata)
    dto.prj = ldd.prj
    # set data
    dto.set_data(grid=grd_outdist)

    filename = "dto_{}".format(project_name)

    # export map
    logger.info("{} {} --- DTO raster map".format(prompt, s_step))
    dto.export(folder=outdir, filename=filename)
    if export_views:
        # export view
        logger.info("{} {} --- DTO raster view".format(prompt, s_step))
        dto.view(show=False, folder=outdir, filename=filename)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(
        "{} {} --- elapsed time: {} seconds".format(
            prompt, s_step, round(elapsed_time, 3)
        )
    )

    # ---------------------- END ----------------------
    end_end = time.time()
    elapsed_time = end_end - start_start
    logger.info(
        "{} total elapsed time: {} seconds".format(prompt, round(elapsed_time, 3))
    )
    logger.info("{} end".format(prompt))
    return 0


if __name__ == "__main__":
    print("HI")
    import matplotlib.pyplot as plt

    plt.style.use("seaborn-v0_8")
