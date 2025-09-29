.. include:: ./includes/external_links.rst

.. include:: ./includes/warning_development.rst

.. _projects:

Projects
#######################################################################

This page describes the **project system** used in ``plans``.

All simulations are organized inside a project, which is a **self-contained file system** with a standardized folder structure. Users must first create or specify a project before running any simulation. Each simulation must specify which scenario and basin combination (climate + land use + basin) to run. All required input data, intermediate caches, and outputs live inside this folder tree.

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

.. _project structure:

Project Structure
=======================================================================

A project is divided into two main parts:

- :ref:`project data folder` — Contains all :ref:`io-input-files` and :ref:`io-intermediate-files` (caches), and configuration tables.
- :ref:`project outputs folder` — Stores all results of simulations and processing operations.

Mandatory folders (``data/`` and ``outputs/``) are created automatically when a project is setup.
Users may add extra folders and files, but the standardized structure must be preserved.


.. _project data folder:

Data Folder
=======================================================================

The ``data/`` folder is where users provide input files and where the model stores
intermediate pre-processing results.

**Subfolders:**

- ``basins/`` — Contains one default project main basin (``main/``) and any number of user-defined catchments. Each simulation must specify which basin to use.
- ``climate/`` — Contains one default climate scenario (``observed/``) and any number of user-defined scenarios. Each simulation must specify which climate scenario to use.
- ``lulc/`` — Similar to climate, with an ``observed/`` folder for historical land-use data and optional land use scenario folders.
- ``soils/`` — Stores soil maps and attributes.
- ``topo/`` — Contains topographic derivatives such as HAND, TWI, and other DEM-derived data.

.. _project basin subfolder:

Basin Subfolder
-----------------------------------------------------------------------

The ``basins/`` folder defines the spatial units of simulation within the project.
Each basin is represented by a **boolean footprint raster** that marks which
raster cells belong to that catchment within the global spatial extent of the project.

By default, a single subfolder called ``main/`` is created when a project is first initialized.
This is intended to hold the **primary basin of interest** for the project — not necessarily the
largest catchment, but the one most relevant for analysis.

Users may create additional subfolders to represent:

- **Sub-catchments** within the project area (for nested or partial-basin simulations)
- **Ungauged catchments** (to run simulations without observed flow data)
- **Multiple gauged basins** (to allow calibration or validation against multiple flow stations)

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
Each operation is saved in its own subfolder, identified by a unique name, ID and timestamp, making it easy to retrieve and compare runs.



