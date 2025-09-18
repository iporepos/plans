.. a cool badge for the source.

.. include:: ./badge_source.rst

.. include:: ./_links.rst

.. _files:

Files
############################################

This is the input and output (I/O) files documentation of ``plans``.

.. attention::

   This section deprecated. Updates soon.

I/O workflow is quite straight forward.
All files are always formatted in only two ways:

- ``csv`` for :ref:`Table<io-table>` structure;
- ``tif`` for :ref:`Raster map<io-raster>` structure.

And there are two categories of files:

- :ref:`Input Files<io-input-files>`: required and optional data files for running ``plans``;
- :ref:`Output Files<io-output-files>`: intermediate and result data files.


Contents
***********************************************************************

.. toctree::
   :maxdepth: 1

   Files <self>
   files_structure
   files_asc


.. _io-input-files:

Input Files
***********************************************************************

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis. Mauris gravida
ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl.

Input files summary
============================================

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis. Mauris gravida
ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl.

+-------------+------------------------+-------------------------------------------------------+
| File        | Structure              | Description                                           |
+=============+========================+=======================================================+
| litho       | Qualitative Raster map | Map of lithological classes                           |
+-------------+------------------------+-------------------------------------------------------+
| soils       | Qualitative Raster map | Map of soil types                                     |
+-------------+------------------------+-------------------------------------------------------+
| dem         | Raster map             | Map of elevation (digital elevation model)            |
+-------------+------------------------+-------------------------------------------------------+
| acc         | Raster map             | Map of accumulated drainage area                      |
+-------------+------------------------+-------------------------------------------------------+
| slope       | Raster map             | Map of slope                                          |
+-------------+------------------------+-------------------------------------------------------+
| ldd         | Raster map             | Map of local drain direction (PC raster convention)   |
+-------------+------------------------+-------------------------------------------------------+
| twi         | Raster map             | Map of Topographical Wetness Index                    |
+-------------+------------------------+-------------------------------------------------------+
| hand        | Raster map             | Map of Height Above the Nearest Drainage              |
+-------------+------------------------+-------------------------------------------------------+
| basins      | Qualitative Raster map | Map of modelled basins                                |
+-------------+------------------------+-------------------------------------------------------+
| outlets     | Qualitative Raster map | Map of basin outlets                                  |
+-------------+------------------------+-------------------------------------------------------+
| stage_*     | Time series            | Time series of river stage                            |
+-------------+------------------------+-------------------------------------------------------+
| basins_info | Attribute table        | Relational table for basins                           |
+-------------+------------------------+-------------------------------------------------------+
| rain_zones  | Qualitative Raster map | Map of rain gauge zones                               |
+-------------+------------------------+-------------------------------------------------------+
| rain_*      | Time series            | Time series of rainfall                               |
+-------------+------------------------+-------------------------------------------------------+
| rain_info   | Attribute table        | Relational table for rain gauges                      |
+-------------+------------------------+-------------------------------------------------------+
| lulc_*      | Qualitative Raster map | Map of Land Use and Land Cover classes                |
+-------------+------------------------+-------------------------------------------------------+
| clim_*      | Time series            | Time series of climatic variables                     |
+-------------+------------------------+-------------------------------------------------------+
| clim_info   | Attribute table        | Relational table for climatic stations                |
+-------------+------------------------+-------------------------------------------------------+
| et_*        | Raster map             | Map of evapotranspiration estimated by remote-sensing |
+-------------+------------------------+-------------------------------------------------------+
| ndvi_*      | Raster map             | Map of the NDVI vegetation index                      |
+-------------+------------------------+-------------------------------------------------------+


Input files catalog
============================================

.. include:: input_catalog.rst


.. _io-interm-files:

Intermediate Files
********************************************

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis. Mauris gravida
ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl.

Intermediate files summary
============================================

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis. Mauris gravida
ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl.

Intermediate files catalog
============================================

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis. Mauris gravida
ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl.


.. _io-output-files:

********************************************
Output Files
********************************************

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis. Mauris gravida
ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl.

Output files summary
============================================

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis. Mauris gravida
ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl.

Output files catalog
============================================

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis. Mauris gravida
ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl.

