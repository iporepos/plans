.. _io-basin:

Basin Area
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``basin.tif``"
   Project Folder, "``{project}/data/basins/{basin}``"
   Data Structure, ":ref:`Raster<io-raster>`"
   Units, "unitless"
   Data Type, "``uint8``"

**Preview**

{>> todo preview}


.. _io-climate_series:

Climate Series
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``climate_series.csv``"
   Project Folder, "``{project}/data/climate/{scenario}``"
   Data Structure, ":ref:`Time Series<io-timeseries>`"

**Required Fields**

.. csv-table::
   :file: ../data/fields_climate_series.csv
   :header-rows: 1
   :widths: auto
   :delim: ;


**Preview**

{>> todo preview}


.. _io-dem:

Digital Elevation Model
------------------------------------------------------------

Pellentesque habitant morbi tristique senectus
et netus et malesuada fames ac turpis egestas. Morbi et tempor sem.
Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - optional"
   File, "``dem.tif``"
   Project Folder, "``{project}/data/topo``"
   Data Structure, ":ref:`Raster<io-raster>`"
   Units, "m"
   Data Type, "``ufloat32``"

**Preview**

{>> todo preview}


.. _io-dist_area_hist:

Distance vs Area Histogram
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "intermediate"
   File, "``dist_area_hist.csv``"
   Project Folder, "``{project}/data/basins/{basin}``"
   Data Structure, ":ref:`Table<io-table>`"

**Required Fields**

.. csv-table::
   :file: ../data/fields_dist_area_hist.csv
   :header-rows: 1
   :widths: auto
   :delim: ;


**Preview**

{>> todo preview}


.. _io-dto:

Distance To Outlet
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "intermediate"
   File, "``dto.tif``"
   Project Folder, "``{project}/data/topo``"
   Data Structure, ":ref:`Raster<io-raster>`"
   Units, "m"
   Data Type, "``ufloat32``"

**Preview**

{>> todo preview}


.. _io-flowacc:

Flow Accumulation
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - optional"
   File, "``flowacc.tif``"
   Project Folder, "``{project}/data/topo``"
   Data Structure, ":ref:`Raster<io-raster>`"
   Units, "m^2"
   Data Type, "``ufloat32``"

**Preview**

{>> todo preview}


.. _io-hand:

Height Above Nearest Drainage
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``hand.tif``"
   Project Folder, "``{project}/data/topo``"
   Data Structure, ":ref:`Raster<io-raster>`"
   Units, "m"
   Data Type, "``ufloat32``"

**Preview**

{>> todo preview}


.. _io-hillshade:

Hill Shade
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - optional"
   File, "``hillshade.tif``"
   Project Folder, "``{project}/data/topo``"
   Data Structure, ":ref:`Raster<io-raster>`"
   Units, "unitless"
   Data Type, "``uint8``"

**Preview**

{>> todo preview}


.. _io-ldd:

Local Drain Direction
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``ldd.tif``"
   Project Folder, "``{project}/data/topo``"
   Data Structure, ":ref:`Quali Raster<io-qualiraster>`"
   Units, "id"
   Data Type, "``uint8``"

**Preview**

{>> todo preview}


.. _io-lulc_attributes:

Land Use Attributes
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``lulc_attributes.csv``"
   Project Folder, "``{project}/data/lulc``"
   Data Structure, ":ref:`Attribute Table<io-attribute>`"

**Required Fields**

.. csv-table::
   :file: ../data/fields_lulc_attributes.csv
   :header-rows: 1
   :widths: auto
   :delim: ;


**Preview**

{>> todo preview}


.. _io-lulc_{date}:

Land Use
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``lulc_{date}.tif``"
   Project Folder, "``{project}/data/lulc/{scenario}``"
   Data Structure, ":ref:`Time Quali Raster<io-timequaliraster>`"
   Units, "id"
   Data Type, "``uint8``"

**Preview**

{>> todo preview}


.. _io-parameters_info:

Parameters of Upscaled Model
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``parameters_info.csv``"
   Project Folder, "``{project}/data``"
   Data Structure, ":ref:`Info Table<io-infotable>`"

**Required Fields**

.. csv-table::
   :file: ../data/fields_parameters_info.csv
   :header-rows: 1
   :widths: auto
   :delim: ;

**Required Horizontal Fields**

.. csv-table::
   :file: ../data/h_fields_parameters_info.csv
   :header-rows: 1
   :widths: auto
   :delim: ;

**Preview**

{>> todo preview}


.. _io-project_info:

Project Specifications
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``project_info.csv``"
   Project Folder, "``{project}/data``"
   Data Structure, ":ref:`Info Table<io-infotable>`"

**Required Fields**

.. csv-table::
   :file: ../data/fields_project_info.csv
   :header-rows: 1
   :widths: auto
   :delim: ;

**Required Horizontal Fields**

.. csv-table::
   :file: ../data/h_fields_project_info.csv
   :header-rows: 1
   :widths: auto
   :delim: ;

**Preview**

{>> todo preview}


.. _io-qobs_series:

Streamflow Data
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - optional"
   File, "``qobs_series.csv``"
   Project Folder, "``{project}/data/basins/{basin}``"
   Data Structure, ":ref:`Time Series<io-timeseries>`"

**Required Fields**

.. csv-table::
   :file: ../data/fields_qobs_series.csv
   :header-rows: 1
   :widths: auto
   :delim: ;


**Preview**

{>> todo preview}


.. _io-slope:

Slope
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis.
Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - optional"
   File, "``slope.tif``"
   Project Folder, "``{project}/data/topo``"
   Data Structure, ":ref:`Raster<io-raster>`"
   Units, "degrees"
   Data Type, "``ufloat32``"

**Preview**

{>> todo preview}


.. _io-soils:

Soils
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``soils.tif``"
   Project Folder, "``{project}/data/soils``"
   Data Structure, ":ref:`Quali Raster<io-qualiraster>`"
   Units, "id"
   Data Type, "``uint8``"

**Preview**

{>> todo preview}


.. _io-soils_attributes:

Soils Attributes
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``soils_attributes.csv``"
   Project Folder, "``{project}/data/soils``"
   Data Structure, ":ref:`Attribute Table<io-attribute>`"

**Required Fields**

.. csv-table::
   :file: ../data/fields_soils_attributes.csv
   :header-rows: 1
   :widths: auto
   :delim: ;


**Preview**

{>> todo preview}


.. _io-tsi:

Topographic Saturation Index
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "intermediate"
   File, "``tsi.tif``"
   Project Folder, "``{project}/data/topo``"
   Data Structure, ":ref:`Raster<io-raster>`"
   Units, "index"
   Data Type, "``uint8``"

**Preview**

{>> todo preview}


.. _io-twi:

Topographic Wetness Index
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``twi.tif``"
   Project Folder, "``{project}/data/topo``"
   Data Structure, ":ref:`Raster<io-raster>`"
   Units, "index"
   Data Type, "``ufloat32``"

**Preview**

{>> todo preview}


.. _io-uparea:

Upslope Area
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - optional"
   File, "``uparea.tif``"
   Project Folder, "``{project}/data/topo``"
   Data Structure, ":ref:`Raster<io-raster>`"
   Units, "m^2"
   Data Type, "``ufloat32``"

**Preview**

{>> todo preview}