.. include:: ./includes/badge_source.rst

.. include:: ./_links.rst

.. _files-data-structures:

Data Structures
############################################

Files used in ``plans`` are related to the following two primitive data structures:

- :ref:`Table<io-table>`;
- :ref:`Raster<io-raster>`.

A :ref:`Table<io-table>` can store a frame of data in rows and columns in a single file.
A :ref:`Raster<io-raster>` can store a map in a matrix/grid of numbers in a single file.

Input files must be formatted in by **standard** way, otherwise the tool is not going to work. The standards are meant to be simple and user-friendly.

.. admonition:: Using open-source applications
   :class: tip

   Open-source applications like `LibreOffice`_ and QGIS_ are very convenient to fit data into ``plans`` standards.

.. _io-table:

Table
============================================

A ``Table`` in ``plans`` is a frame of data defined by rows and columns. Each column represents a **field** that must be *homogeneous*. This means that each field stores the same :ref:`data type<io-data-type>`. The first row stores the names of the fields. The subsequent rows stores the data itself.

Tables must follow this general rules:

#. [mandatory] file extension: ``.csv``;
#. [mandatory] homogeneous data type for on each column;
#. [mandatory] column separator: semi-colon ``;``;
#. [mandatory] decimal separator for numbers: ``.``.

For example, in the following table ``id`` is an integer number field, ``ndvi_mean`` is a real number field and the remaining are text fields.

.. code-block:: text

   id;     name; alias;    color;  ndvi_mean
    1;    Water;     W;     blue;       -0.9
    2;   Forest;     F;    green;       0.87
    3;    Crops;     C;  magenta;       0.42
    4;  Pasture;     P;   orange;       0.76
    5;    Urban;     U;   9AA7A3;       0.24


.. admonition:: Column names standards
   :class: warning

   Field/column names may follow standards also, see below.


.. _io-timeseries:

Time Series
--------------------------------------------

A :ref:`Time Series<io-timeseries>` in ``plans`` is a special kind of :ref:`Table<io-table>` file that must have a ``datetime`` text field (preferably in the first column).

Time Series must follow this rules:

#. [mandatory] ``datetime`` text field (preferably in the first column);
#. [recommended] ``datetime`` formatted in `ISO 8601`_: ``yyyy-mm-dd HH:MM:SS.SSS`` (year, month, day, hour, minute and seconds).
#. [recommended] homogeneous datetime frequency (every 15 min, hourly, daily, etc).
#. [recommended] no gaps or voids in data.

The other fields than ``datetime`` generally are real number fields that stores the state of **variables** like precipitation ``ppt`` and surface air temperature ``tas``. Time Series files tends to have a large number of rows. The first 10 rows of a daily Time Series file looks like this:

.. code-block:: text

                  datetime;  ppt;  tas
   2020-01-01 00:00:00.000;  0.0; 20.1
   2020-01-02 00:00:00.000;  5.1; 24.3
   2020-01-03 00:00:00.000;  0.0; 25.8
   2020-01-04 00:00:00.000; 12.9; 21.4
   2020-01-05 00:00:00.000;  0.0; 21.5
   2020-01-06 00:00:00.000;  0.0; 23.6
   2020-01-07 00:00:00.000;  8.6; 20.6
   2020-01-08 00:00:00.000;  4.7; 28.3
   2020-01-09 00:00:00.000;  0.0; 27.1
                      ... ;  ...; ...

.. admonition:: Automatic fill of time information
   :class: note

   During processing, ``plans`` will fill *time* information (hours, minute and seconds) if only the *date* is passed (year, month and day), like in the above example.


``Time Series`` also have a **datetime frequency**. Recommended frequencies:

- 15 minutes;
- 20 minutes;
- 30 minutes;
- Hourly;
- Daily.

.. admonition:: Shorter and longer frequencies
   :class: warning

   Shorter frequencies than 15 min are not recommended due to processing performance. Longer frequencies than 1 day are not recommended due to effective hydrological process representation.


.. admonition:: Small gaps and voids in Time Series
   :class: important

   ``plans`` will try to fill or **interpolate** small gaps and voids in a given Time Series. However, be aware that this may cause unnoticed impacts on model outputs. A best practice is to interpolate and fill voids *prior* to the processing so users can understand what is going on.

   For instance, consider the following ``Time Series`` that has a **gap** (missing Jan/3 and Jan/4 dates) and a **void** for ``ppt`` in Jan/8:

   .. code-block::
     :emphasize-lines: 3,4,7

                    datetime;  ppt;  tas
     2020-01-01 00:00:00.000;  0.0; 20.1
     2020-01-02 00:00:00.000;  5.1; 24.3
     2020-01-05 00:00:00.000;  0.0; 21.5
     2020-01-06 00:00:00.000;  0.0; 23.6
     2020-01-07 00:00:00.000;  8.6; 20.6
     2020-01-08 00:00:00.000;     ; 28.3
     2020-01-09 00:00:00.000;  0.0; 27.1

   In this case, ``plans`` would interpolate temperature ``tas`` and fill with 0 the precipitation ``ppt``:

   .. code-block::
       :emphasize-lines: 4,5,8

                      datetime;  ppt;  tas
       2020-01-01 00:00:00.000;  0.0; 20.1
       2020-01-02 00:00:00.000;  5.1; 24.3
       2020-01-03 00:00:00.000;  0.0; 23.3
       2020-01-04 00:00:00.000;  0.0; 22.4
       2020-01-05 00:00:00.000;  0.0; 21.5
       2020-01-06 00:00:00.000;  0.0; 23.6
       2020-01-07 00:00:00.000;  8.6; 20.6
       2020-01-08 00:00:00.000;  0.0; 28.3
       2020-01-09 00:00:00.000;  0.0; 27.1


.. _io-attribute:

Attribute Table
--------------------------------------------

An :ref:`Attribute Table<io-attribute>` is a special kind of :ref:`Table<io-table>` that stores extar information about maps.

**Basic required fields**

.. csv-table::
   :header: "Name", "Description", "Data Type", "Units"
   :widths: 10, 40, 15, 15

   ``id``, "Unique numeric code", ``int``, index
   ``name``, "Unique name", ``str``, n.a.
   ``alias``, "Unique short nickname or label", ``str``, n.a.
   ``color``, "Color HEX code or name available in `Matplotlib`_", ``str``, n.a.


**Extra required fields** may be also needed, depending on each input data.

Example of an ``Attribute Table``:

.. code-block:: text

   id;     name; alias;    color;  ndvi_mean
    1;    Water;     W;     blue;       -0.9
    2;   Forest;     F;    green;       0.87
    3;    Crops;     C;  magenta;       0.42
    4;  Pasture;     P;   orange;       0.76
    5;    Urban;     U;  #9AA7A3;       0.24


.. admonition:: ``plans`` is case-sensitive
   :class: warning

   Upper case and lower case matters. ``Name`` is different than ``name``.


.. admonition:: Add non-required fields
   :class: tip

   Any other fields (columns) other than the required will be ignored so  you can add convenient and useful extra non-required fields. For instance, here a ``description`` text field was added for holding more information about each land use class:

   .. code-block:: text

      id;     name; alias;    color;   ndvi_mean                          description
       1;    Water;     W;     blue;       -0.9;              Lakes, rivers and ocean
       2;   Forest;     F;    green;       0.87;     Forests (natural and cultivated)
       3;    Crops;     C;  magenta;       0.42;            Conventional annual crops
       4;  Pasture;     P;   orange;       0.76;  Conventional pasture and grasslands
       5;    Urban;     U;   9AA7A3;       0.24;                      Developed areas


.. _io-raster:

Raster
============================================

A **Raster** in ``plans`` is a map of data defined by a matrix or grid of cells
storing numbers (int or float) and encoded in way that it can be
georreferenced in a given Coordinate Reference System (``CRS``).

Single Raster files must follow this general rules:

#. [mandatory] :ref:`GeoTIFF file<io-tif-file>` with ``.tif`` extension;
#. [recommended] projected ``CRS`` so all cells are measured in meters;

Multiple Raster files must follow this general rules:

#. [mandatory] files are aligned for the same spatial extension;
#. [mandatory] files are aligned for the same spatial resolution;

.. admonition:: Grid shape must be the same
   :class: important

   The rule for multiple files implies that all ``Raster`` files in a given project must share the same grid shape (number or rows and columns).


.. _io-tif-file:

GeoTIFF format
--------------------------------------------

The `GeoTIFF`_ format is the standard ``Raster`` file in ``plans``.
This is a well-known raster file distributed by most of dataset providers.

The advantages of ``GeoTIFF`` is that it stores data and metadata together in the same file.
``plans`` parse ``GeoTIFF`` files using the `Rasterio`_ libray.

.. admonition:: GDAL reference
   :class: seealso

   More details about the `GeoTIFF file`_ is given in GDAL documentation.


.. _io-timeraster:

Time Raster
--------------------------------------------

A ``Time Raster`` in ``plans`` is a special kind of :ref:`Raster<io-raster>` file in which the data refers to a **snapshot of the time line**.

Single Time Raster files must follow this general rules:

#. [mandatory] :ref:`GeoTIFF file<io-tif-file>`;
#. [mandatory] named with a date-time suffix separated by underscore ``_``: ``map_2021-09-02.tif``;
#. [recommended] projected ``CRS`` so all cells are measured in meters;

Same rules applies for multiple files.

For instance, Land Use Land Cover is a spatial data that may require many Time Raster files:

.. code-block:: bash

   {folder}/
      ├── lulc_2020.tif       # Raster - Land Use in 2020
      ├── lulc_2021.tif       # Raster - Land Use in 2021
      └── lulc_2022.tif       # Raster - Land Use in 2022



.. _io-qualiraster:

Quali Raster
--------------------------------------------

A Quali Raster in ``plans`` is a special kind of :ref:`Raster<io-raster>` file in which data is qualitative (classes or ids), and an auxiliary :ref:`Attribute Table<io-attribute>` must be provided.

Single ``Quali Raster`` files must follow this general rules:

#. [mandatory] a :ref:`GeoTIFF file<io-tif-file>` for map data;
#. [mandatory] an :ref:`Attribute Table<io-attribute>`;
#. [recommended] projected ``CRS`` so all cells are measured in meters;

Same rules applies for multiple files.

For instance, a ``Quali Raster`` for Land Use Land Cover only stores the ``id`` code for each land use class. More information and parameters must be stored in the auxiliar ``Attribute Table``.

.. code-block:: bash

   {folder}/
      ├── lulc_2020.tif       # Raster - Land Use in 2020
      └── lulc_info.csv       # <-- Attribute Table

.. admonition:: One ``Attribute Table`` can feed many maps
   :class: note

   The same ``Attribute Table`` file can supply the information required of many ``Raster`` maps.
   For instance, consider a set of 3 Land Use Land Cover maps, for different years.
   They all can use the same ``Attribute Table`` file:

   .. code-block:: bash

      {folder}/
          ├── lulc_2020.tif
          ├── lulc_2021.tif
          ├── lulc_2022.tif
          └── lulc_info.csv       # <-- Attribute Table


.. _io-timequaliraster:

Time Quali Raster
--------------------------------------------

A ``Time Quali Raster`` in ``plans`` is a special kind of :ref:`Raster<io-raster>` file that arises when the map is both a :ref:`Time Raster<io-timeraster>` and a :ref:`Quali Raster<io-qualiraster>`. Land Use maps are the classical example, as shown above.


.. _io-data-type:

Data Types
============================================

Data Type is the encoding of data at the hardware level. For beginners, one may understand data types by this primitive classification:

- ``str`` text string: common text characters;
- ``int`` integer numbers: 2, 0, 1000;
- ``float`` real numbers: 1.2, -3.44.

.. admonition:: Detailed data types
   :class: important

   The data types listed above are very primitive. For instance, ``int`` can be ``int8`` or ``int64``, which yield a big difference in memory usage. :ref:`See below<io-data-type-reference>` for a comprehensive reference.


.. _io-data-type-nodata:

No-data value convention
--------------------------------------------

A ``nodata`` value is a convention of what values in data means that there are actually *no data* (a data void). For tables, this is usually set as empty cells or some text like "N.A." (not-apply, etc). For raster maps, the ``GeoTIFF`` format has a built-in metadata that stores a ``nodata`` value.

.. admonition:: Enforcement of ``nodata``
   :class: warning

   Users are *not* required to set ``nodata`` values, but the incoming values may be overwritten to ``plans`` standard convention.


.. _io-data-type-reference:

Data Types Reference
--------------------------------------------

.. csv-table:: Data Types Reference Table
   :file: ./data/dtypes.csv
   :header-rows: 1
   :widths: auto
   :delim: ;


.. note::

   Hi-order values in the above table are approximations. For example, the exact upper value of ``int32`` is 4,294,967,295.



.. admonition:: NumPy Data Types
   :class: seealso

   Check out `NumPy Data Types`_ documentation page for mode details for data types in Python arrays.


.. admonition:: GDAL Data Types
   :class: seealso

   Check out `GDAL Data Types`_ documentation page for mode details for data types in raster maps.