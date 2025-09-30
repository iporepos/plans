.. include:: ./includes/external_links.rst

.. include:: ./includes/warning_development.rst

.. _examples:

Examples
#######################################################################

This page show hands-on examples and tutorials for running ``plans``.

.. admonition:: Install ``plans``
   :class: seealso

   Check out :ref:`installation` section in the :ref:`userguide`.

.. _example projects setup:

Setting up projects
***********************************************************************

Import ``plans``

.. code-block:: python

    import plans

.. _example projects new:

New project
========================================================================

Set new project details in a python ``dict``:

.. code-block:: python

    # [CHANGE THIS] setup specs dictionary
    project_specs = {
        "folder_base": "C:/plans", # change this path
        "name": "newProject",
        "alias": "NPrj",
        "source": "Me",
        "description": "Just a test"
    }

Then call ``plans.new_project()``

.. code-block:: python

    plans.new_project(specs=project_specs)

This will make a new project in the base folder provided.

.. warning::

   An error is raised if a project already exists with this name.

This syntax creates and load to a variable the ``plans.Project`` instance:

.. code-block:: python

    prj = plans.new_project(specs=project_specs)

.. _example projects load:

Load project
========================================================================

Call ``plans.load_project()``

.. code-block:: python

    prj = plans.load_project(project_folder="C:/plans/NewProject")


