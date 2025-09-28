.. include:: ./includes/external_links.rst

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
        │     ├── parameters_info.csv
        │     │
        │     ├── basins/
        │     │     ├── main/          # default basin
        │     │     ├── {basin}/       # user-defined basin
        │     │     │     ├── basin.tif
        │     │     │     └── qobs_series.csv
        │     │     └── ...
        │     ├── climate/
        │     │     ├── observed/      # default scenario
        │     │     │     └── climate_series.csv
        │     │     ├── {scenario}/    # user-defined scenarios
        │     │     └── ...
        │     ├── lulc/ (land use data)
        │     │     ├── observed/      # default scenario
        │     │     │     ├── lulc_attributes.csv
        │     │     │     ├── lulc_{date}.tif
        │     │     │     └── ...
        │     │     ├── {scenario}/    # user-defined scenarios
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

