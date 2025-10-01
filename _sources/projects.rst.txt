.. include:: ./includes/external_links.rst

.. include:: ./includes/warning_development.rst

.. _projects:

Projects
#######################################################################

This page describes the **project system** used in ``plans``.

.. seealso::

   Check out the :ref:`files` page for more details on how to setup input data.

The ``plans`` system for projects works following this general rules:

**Standard file system**

A project has a standard file system, with expected folder and file names
in an expected nesting pattern. Standard components may be required or optional (extra).
Non-standard components are ignored.

**Self-contained file system**

A project is self-contained, since all files and outputs for running ``plans`` live inside a project.
Users must first create or specify/load a project before running any analysis or simulation.

**One area of interest**

A project is defined for a single area of interest ``AOI``. This means that all data is related
to a rectangular spatial extension. Maps must share the same extension.
This can account for multiple basins within the ``AOI``.

**Simulation combinations**

A model simulation in a project is defined by a scenario and basin combination.
So every run is referred to a climate + land use + basin combination.


.. _project structure:

Project Structure
=======================================================================

A project is divided into two main parts:

- :ref:`project data folder` — Contains all :ref:`io-input-files` and :ref:`io-intermediate-files`.
- :ref:`project outputs folder` — Stores all results of simulations and processing operations.

Mandatory folders (``data/`` and ``outputs/``) are created automatically when a project is setup.
Users may add extra folders and files, but the standardized structure must be preserved.

The project tree of looks like this:

.. code-block:: bash

   {project}/
        ├── data/
        │     ├── project_info.csv
        │     ├── parameters_info.csv
        │     │
        │     ├── basins/
        │     │     ├── main/                   # default basin
        │     │     ├── {basin}/                # user-defined basin
        │     │     │     ├── basin.tif
        │     │     │     └── qobs_series.csv
        │     │     └── ...
        │     ├── climate/
        │     │     ├── observed/               # default scenario
        │     │     │     └── climate_series.csv
        │     │     ├── {climate-scenario}/     # user-defined scenarios
        │     │     └── ...
        │     ├── lulc/
        │     │     ├── observed/               # default scenario
        │     │     │     ├── lulc_attributes.csv
        │     │     │     ├── lulc_{date}.tif
        │     │     │     └── ...
        │     │     ├── {lulc-scenario}/        # user-defined scenarios
        │     │     └── ...
        │     ├── soils/
        │     │     ├── soils_attributes.csv
        │     │     └── soils.tif
        │     └── topo/
        │           ├── hand.tif
        │           ├── twi.tif
        │           ├── ldd.tif
        │           └── ...
        │
        └── outputs/
              └── ...

.. _project data folder:

Data Folder
=======================================================================

The ``data/`` folder is where users provide input files and where the model stores
intermediate pre-processing results.

**Data standard subfolders:**

- ``basins/`` — Contains one standard project main basin (``main/``) and any number of user-defined catchments. Each simulation must specify which basin to use.
- ``climate/`` — Contains one default climate scenario (``observed/``) and any number of user-defined scenarios. Each simulation must specify which climate scenario to use.
- ``lulc/`` — Similar to climate, with a default ``observed/`` folder for historical land-use data and optional land use scenario folders.
- ``soils/`` — Stores soil maps and attributes.
- ``topo/`` — Contains topographic derivatives such as HAND, TWI, and other DEM-derived data.

.. _project subfolders:

Optional subfolders
-----------------------------------------------------------------------

Users may create optional subfolders under ``basins/``, ``climate/`` and
``lulc/`` data folders. Any name for this subfolders is possible,
but must be just one word with ASCII characters.

.. admonition:: Naming subfolders with just one word
  :class: danger

  Subfolders must be named with a single word with ASCII characters:

  .. code-block:: bash

     └── scenario01  # this folder name is ok

  Special characters, blank spaces, underscores and hyphen are **not allowed**.

  .. code-block:: bash

     └── my ipcc-scenario_01  # not allowed folder name

  This rule is intended to avoid disrupting file name patterns and command line strings.


.. _project basin subfolder:

Basin Subfolder
-----------------------------------------------------------------------

The ``basins/`` folder defines the units of simulation within the project.
Each basin is represented by a **boolean footprint raster** that marks which
raster cells belong to that catchment within the global spatial extent of the project.

.. admonition:: Main basin standard subfolder
  :class: important

  Data for the **main basin** of a project is expected to live in a subfolder named ``main/``.
  This is intended to hold the **primary basin of interest** for the project — not necessarily the
  largest or gauged catchment, but the one most relevant for the project analysis.

Users may create additional subfolders to represent:

- **Sub-basins** within the project area (for nested or partial-basin simulations)
- **Multiple gauged basins** (to allow calibration or validation against multiple flow stations)
- **Ungauged basins** (to run simulations without observed flow data)

Each basin folder may contain:

- Required and optional input files
- Intermediate files computed by the model
- Metadata or additional supporting files as needed

Simulations must always reference a specific basin folder, allowing users to run scenarios
for different spatial subsets of the project area.

.. _project scenario subfolder:

Scenario Subfolder
-----------------------------------------------------------------------

The ``climate/`` and ``lulc/`` subfolders define **scenarios** used in simulations.
A scenario is a named folder containing all input data for a specific **climate** or **land-use** condition.

By default, a subfolder called ``observed/`` is created for both climate and land use.
This is intended to store **historical or baseline data** used as the reference case for simulations.

.. note::

   There is no standard expected name for scenarios. The default ``observed/`` is only
   a name suggestion.

Users may create additional scenario folders to represent:

- **Alternative climate conditions** (e.g., future projections, synthetic weather series)
- **Alternative land-use configurations** (e.g., reforestation plans, urban expansion)
- **What-if analyses** combining different climate and land-use assumptions

Each scenario subfolder may contain:

- Required and optional input files for that scenario (e.g., climate series, land-use rasters)
- Intermediate files computed by the model
- Metadata or additional supporting files as needed

Simulations must always specify which scenario(s) to use.
Climate and land-use scenarios can be freely combined, allowing users to explore
multiple "what-if" configurations within a single project.

.. _project outputs folder:

Outputs Folder
=======================================================================

The ``outputs/`` folder stores results from all simulation and processing runs.
Each processing operation is saved in its own subfolder, identified by ``{process-name}_{timestamp}/``, making it easy to retrieve and compare runs.

.. _project convention:

Non-required subfolders and files
=======================================================================

All required folders in a project may hold extra subfolders or files for helping to organize data
and integrate with data processing pipelines. Non-required subfolders are ignored by ``plans``.

However, for the purpose of data sharing, we recommend to create subfolders always in the ``{project}/data/`` folder and following this naming convention:

- ``data/{project}.gpkg`` - a geopackage file designed to store vector layers and QGIS projects
- ``src/`` - a subfolder to store sourced files that are not yet in the ``plans`` standard format.
  These files may be converted to the standard format via custom scripts
- ``scripts/`` - a subfolder with file scripts
- ``misc/`` - a subfolder designed to store miscellaneous files
- ``temp/`` - a subfolder designed to store temporary files
- ``old/`` - a subfolder designed to store deprecated files

.. admonition:: Underscore prefix ``_``
   :class: tip

   A possible extension of this convention is to include an underscore prefix ``_`` denoting a non-required folder, e.g., ``data/_src/``. This prefix will visually split the non-required folders from the required ones.


.. admonition:: Basin, Land use and Climate subfolders are reserved for basins and scenarios
   :class: danger

   Do not create subfolders in ``data/basins``, ``data/lulc`` and ``data/climate``. These are always interpreted as basins or scenarios folders.

Example of a project structure with extra folders

.. code-block:: bash

   myproject/
        ├── data/
        │     ├── myproject.gpkg               # GIS layers and projects
        │     │
        │     │ # ------ required data
        │     ├── project_info.csv
        │     ├── parameters_info.csv
        │     │
        │     │ # ------ non-required folders
        │     ├── _scripts/
        │     │      └── convert_dem_to_ldd.py  # script
        │     ├── _src/
        │     │      └── dem_large.tif          # sourced data
        │     ├── _temp/
        │     │
        │     │ # ------ required folders
        │     ├── basins/
        │     ├── climate/
        │     ├── lulc/
        │     ├── soils/
        │     └── topo/
        │
        └── outputs/
              └── ...




