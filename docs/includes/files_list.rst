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


Climate Forcing
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - optional"
   File, "``climate.csv``"
   Project Folder, "``{project}/data/climate/{scenario}``"
   Data Structure, ":ref:`Time Series<io-timeseries>`"

**Required Fields**

.. csv-table::
   :file: ../data/fields_climate.csv
   :header-rows: 1
   :widths: auto
   :delim: ;


**Preview**

{>> todo preview}


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


Histogram Distance vs Area
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "intermediate"
   File, "``hist_dist_area.csv``"
   Project Folder, "``{project}/data/basins/{basin}``"
   Data Structure, ":ref:`Table<io-table>`"

**Required Fields**

.. csv-table::
   :file: ../data/fields_hist_dist_area.csv
   :header-rows: 1
   :widths: auto
   :delim: ;


**Preview**

{>> todo preview}


Local Drain Direction
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``ldd.tif``"
   Project Folder, "``{project}/data/topo``"
   Data Structure, ":ref:`Raster<io-raster>`"
   Units, "id"
   Data Type, "``uint8``"

**Preview**

{>> todo preview}


Land Use Attributes
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``lulc_info.csv``"
   Project Folder, "``{project}/data/lulc``"
   Data Structure, ":ref:`Attribute Table<io-attribute>`"

**Required Fields**

.. csv-table::
   :file: ../data/fields_lulc_info.csv
   :header-rows: 1
   :widths: auto
   :delim: ;


**Preview**

{>> todo preview}


Land Use
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - optional"
   File, "``lulc_{date}.tif``"
   Project Folder, "``{project}/data/lulc/{scenario}``"
   Data Structure, ":ref:`Time Quali Raster<io-timequaliraster>`"
   Units, "id"
   Data Type, "``uint8``"

**Preview**

{>> todo preview}


Model Upscaled Parameters
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``parameters.csv``"
   Project Folder, "``{project}/data``"
   Data Structure, ":ref:`Table<io-table>`"

**Required Fields**

.. csv-table::
   :file: ../data/fields_parameters.csv
   :header-rows: 1
   :widths: auto
   :delim: ;


**Preview**

{>> todo preview}


Project Info Table
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``project_info.csv``"
   Project Folder, "``{project}/data``"
   Data Structure, ":ref:`Table<io-table>`"

**Required Fields**

.. csv-table::
   :file: ../data/fields_project_info.csv
   :header-rows: 1
   :widths: auto
   :delim: ;


**Preview**

{>> todo preview}


Observed Streamflow
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - optional"
   File, "``q_obs.csv``"
   Project Folder, "``{project}/data/basins/{basin}``"
   Data Structure, ":ref:`Time Series<io-timeseries>`"

**Required Fields**

.. csv-table::
   :file: ../data/fields_q_obs.csv
   :header-rows: 1
   :widths: auto
   :delim: ;


**Preview**

{>> todo preview}


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
   Data Structure, ":ref:`Quali Raster<io-qualiraster>`"
   Units, "degrees"
   Data Type, "``ufloat32``"

**Preview**

{>> todo preview}


Soils Map
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``soils.tif``"
   Project Folder, "``{project}/data/soils``"
   Data Structure, ":ref:`Raster<io-raster>`"
   Units, "id"
   Data Type, "``uint8``"

**Preview**

{>> todo preview}


Soils Attributes
------------------------------------------------------------

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam, in porttitor lacus lobortis vitae. In a lacinia nisl. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi et tempor sem. Nullam quam dolor, venenatis eget magna ut, accumsan mollis erat.

**Specifications**

.. csv-table::
   :widths: auto

   Workflow, "input - required"
   File, "``soils_info.csv``"
   Project Folder, "``{project}/data/soils``"
   Data Structure, ":ref:`Attribute Table<io-attribute>`"

**Required Fields**

.. csv-table::
   :file: ../data/fields_soils_info.csv
   :header-rows: 1
   :widths: auto
   :delim: ;


**Preview**

{>> todo preview}


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