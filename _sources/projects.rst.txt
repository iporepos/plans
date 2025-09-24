.. include:: ./_links.rst

.. include:: ./includes/warning_development.rst

.. _projects:

Projects
#######################################################################

This is the project reference documentation of ``plans``.

.. include:: ./includes/ipsum.rst


.. code-block:: bash

   {project}/
        ├── data/
        │     ├── project_info.csv
        │     ├── parameters.csv
        │     │
        │     ├── basins/
        │     │     ├── basin.tif
        │     │     ├── q_obs.csv
        │     │     └── ...
        │     ├── climate/
        │     │     ├── climate_observed.csv
        │     │     └── ...
        │     ├── lulc/
        │     │     ├── observed/
        │     │     │     ├── lulc_info.csv
        │     │     │     ├── lulc_{date}.tif
        │     │     │     └── ...
        │     │     └── ...
        │     ├── soils/
        │     │     ├── soils_info.csv
        │     │     └── soils.tif
        │     └── topo/
        │           ├── hand.tif
        │           ├── twi.tif
        │           ├── ldd.tif
        │           └── ...
        │
        └── outputs/
              └── ...

