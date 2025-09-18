.. a cool badge for the source.

.. include:: ./badge_source.rst

.. include:: ./_links.rst

.. _usage:

User Guide
#######################################################################

.. attention::

   This section is under active development.


Contents
***********************************************************************

.. toctree::
   :maxdepth: 1

   Usage <self>
   files
   projects


.. _quickview:

Overview
***********************************************************************

``plans`` is open-source, cross-platform tool that is built on top of `Python`_ and some common
dependencies, like `NumPy`_, `SciPy`_, `Matplotlib`_, `Pandas`_ and `Rasterio`_.

This means that ``plans`` can be run in any operational system, locally or remotely,
as long as Python is installed.

Users are encouraged to run ``plans`` under interactive Python environments, like `Jupyter`_
or `Colab`_ notebooks. These platforms are very intuitive for beginners and remove the burden of
setting Python environments.

.. seealso::

   For those who want to *contribute* to ``plans``, see :ref:`Development <development>`


.. _typical workflow:

Typical workflow
***********************************************************************


Typically, to run ``plans`` users may go through the following steps (with some iteration):

Setup data and project
=======================================================================
1. **Gather input data**. Collect observed and scenario data for an **Area Of Interest** (``AOI``).
2. **Pre-process input data**. Files must fits into ``plans`` standards.
3. **Organize input data**. ``plans`` expects data of the ``AOI`` to be organized in a **Project** (a folder system).

Processing data
=======================================================================
5. Use ``plans`` for **data assessments**.
6. Use ``plans`` for **parameter estimation**.
7. Use ``plans`` for **scenario simulation**.

Post-processing
=======================================================================
8. Use extra tools for more visualization and analysis of output data.


.. _installation:

Installation
***********************************************************************

On a Python environment, install ``plans`` via terminal:

.. code-block:: console

    python -m pip install git+https://github.com/iporepos/plans.git@main


On `Jupyter`_ or `Colab`_, run this command on a cell:

.. code-block:: console

    %pip install git+https://github.com/iporepos/plans.git@main


This installation is also enough for installing all dependencies needed for running ``plans``.


.. _setup:

Setup
***********************************************************************

.. _data:

Input data
========================================================================
Required input data are basically two types of files: **tables** and **raster maps**.
Tables are formatted in ``.csv`` and raster files are formatted in ``.tif``.

.. seealso::

   Input data formatting is explained in more detail in :ref:`Files <files>`


.. _project:

Projects
========================================================================
A *project* in ``plans`` is a standard file system that is considered the root for all
operations in a given *session*. Folders and files names or patterns are pre-defined so ``plans``
automatically finds their existence for processing.

Once data is gathered, users are required to populate the folders of a project in the
right folder. For instance, rain data tables of a scenario must go in the ``clim`` folder.
Topographical maps must go in the ``topo`` folder, etc.

.. seealso::

   Project layout and standards is explained in more detail in :ref:`Projects <projects>`




