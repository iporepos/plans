.. include:: ./includes/external_links.rst

.. include:: ./includes/warning_development.rst

.. _userguide:

User Guide
#######################################################################

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

Install as a Python package
============================================

For Python regular users, install the latest package deploy
to a Python 3 environment via pip:

.. code-block:: console

    python -m pip install copyme

Or any desired branch or version via github url:

.. code-block:: console

    python -m pip install git+https://github.com/iporepos/copyme.git@main

On a `Jupyter`_ or `Colab`_ environment, run this command on a cell:

.. code-block:: console

    %pip install plans


Install as a Tool for Windows
============================================

For users seeking only the tool experience in Windows:

1. Make sure the latest Python 3 is installed and added to PATH: https://www.python.org

2. Download the installer PowerShell file ``install-plans.ps1`` from the GitHub repository;

3. Right-click the installer file and click the option ``Run with PowerShell``;

4. Follow the instructions prompted until the end;

**Application folder**

The application tool will live in ``C:\Users\{You}\AppData\Local\plans``.

To check if the app is alive, open ``PowerShell`` and type:

.. code-block:: console

    plans check

The output should result in no error or warning.

**Projects root**

By default, projects for ``plans`` will live under ``C:\Users\{You}\PlansProjects``.

Change the projects root location by editing the ``projects-root.txt`` file located at ``C:\Users\{You}\AppData\Local\plans``

**Update or uninstall**

To update the current installation, just install again from the latest version.
The existing version will be overwritten.

To uninstall, open ``PowerShell`` and type:

.. code-block:: console

    plans uninstall

.. note::

   For a complete purge, manually remove ``plans`` from Windows PATH


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