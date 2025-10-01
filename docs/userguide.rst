.. include:: ./includes/external_links.rst

.. include:: ./includes/warning_development.rst

.. _userguide:

User Guide
#######################################################################

.. _quickview:

Overview
***********************************************************************

``plans`` is open-source, cross-platform tool that is built on top of `Python`_
and some common dependencies, like `NumPy`_, `SciPy`_, `Matplotlib`_, `Pandas`_ and `Rasterio`_.

This means that ``plans`` can be run in any operational system, locally
or remotely, as long as Python is installed.

Users are encouraged to run ``plans`` under interactive Python environments,
like `Jupyter`_ or `Colab`_ notebooks. These platforms are very intuitive
for beginners and remove the burden of setting Python environments.

.. seealso::

   For those who want to *contribute* to ``plans``, see :ref:`Development <development>`


.. _installation:

Installation
***********************************************************************

On a Python environment, install ``plans`` via terminal:

.. code-block:: console

    python -m pip install git+https://github.com/iporepos/plans.git@main


On `Jupyter`_ or `Colab`_, run this command on a cell:

.. code-block:: console

    %pip install git+https://github.com/iporepos/plans.git@main


This installation procedure is also enough for installing all dependencies needed for running ``plans``.





.. _user guide workflow:

Workflow
***********************************************************************

The workflow of ``plans`` is based on the concept of **project**. That
means that all **input data** required must be organized in a **standard file system**.
Once all is set, users can run simulations without specifying entries all the time.

Typically, to run ``plans`` users may go through the following steps (with some iteration):

**Setting up a project**

1. **Gather input data**. Collect observed and scenario data for an **Area Of Interest** (``AOI``).
2. **Pre-process input data**. Files must fits into ``plans`` standards.
3. **Organize input data**. ``plans`` expects data of the ``AOI`` to be organized in a **Project** (a standard file system).

**Processing data**

5. Use ``plans`` for **data assessments**.
6. Use ``plans`` for **parameter estimation**.
7. Use ``plans`` for **scenario simulation**.

**Post-processing**

8. Use extra tools for more visualization and analysis of output data.


.. _user guide setup:

Setup
***********************************************************************

.. _user guide project:

Projects
========================================================================
A **project** in ``plans`` is a standard file system that is considered
the root for all operations in a given *processing session*. Folders and
files names or patterns are pre-defined so ``plans`` automatically finds
their existence for processing.

Once data is gathered, users are required to populate the folders of a
project with standard files. For instance, rain data tables of a scenario
must live in the ``climate`` folder. Topographical maps must go in the
``topo`` folder, etc.

.. admonition:: Working with projects
   :class: seealso

   Check out the :ref:`projects` page for more details on how to setup projects.


.. _user guide data:

Input data
========================================================================
Required input data are basically two types of files: **tables** and **raster maps**.
Tables are formatted in ``.csv`` and raster files are formatted in ``.tif``.

.. admonition:: Working with input data
   :class: seealso

   Check out the :ref:`files` page for more details on how to setup input data.


.. _user guide examples:

Tutorials
***********************************************************************

.. include:: ./includes/ipsum.rst

.. admonition:: Hands-on tutorials
   :class: seealso

   Check out the :ref:`examples` page for hands-on examples.


.. toctree::
   :maxdepth: 1
   :hidden:

   files
   projects
   examples