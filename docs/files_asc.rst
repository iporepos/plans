.. a cool badge for the source.

.. include:: ./badge_source.rst

.. include:: ./_links.rst

----

.. _files-asc:

ASCII format
############################################

The ASCII/AAIGrid is a Raster format simpler than :ref:`GeoTIFF file<io-tif-file>`.
This format require at least two files:

- [mandatory] the main :ref:`Grid file<io-asc-file>`  (``.asc`` extension);
- [optional] the auxiliary :ref:`Grid file<io-prj-file>`  (``.prj`` extension);

.. admonition:: GDAL reference
   :class: seealso

   More details about the `ASCII file`_ is given in GDAL documentation.

.. _io-asc-file:

ASCII file
============================================

The ASCII file stores most relevant information about the map.
Formatting must follow this rules:

- the file must be a plain file with ``.asc`` extension
- the first 6 lines must encode a **heading**, specifying the following metadata:
    - ``ncols``: ``int`` columns of the matrix
    - ``nrows``: ``int``  rows of the matrix
    - ``xllcorner``: ``float`` X (longitude) of the lower left corner in the CRS units (meters or degrees)
    - ``yllcorner``: ``float`` Y (longitude) of the lower left corner in the CRS units (meters or degrees)
    - ``cellsize``: ``uint`` cell resolution in the CRS units (meters or degrees)
    - ``NODATA_value``: ``float`` encoding cells with no data
- after the first 6 lines, the matrix cells must be arranged using blank spaces for value separation.
- period ``.`` must be the separator of decimal places for real numbers

Raster maps tends to have a large number of rows and columns.
The first 10 rows and columns of a ``.asc`` raster file looks like this:

.. code-block:: text

    ncols        311
    nrows        375
    xllcorner    347528.8
    yllcorner    6714069.8
    cellsize     30.0
    NODATA_value -1
     297 305 317 331 347 360 370 382 403 414 ...
     298 307 321 336 353 368 381 398 411 422 ...
     298  -1 321 338 356 372 385 400 415 427 ...
     297  -1 319 334 353 370 381 395 410 423 ...
     296 305 316 334 351 366 376 386 398 416 ...
     294 303 316 333 347 358 368 379 394 409 ...
     290 299 312 328 342 351 361 375 392 407 ...
     288 297 308 320 333 344 358 375 394 410 ...
     287 297 308 319 329 343 362 382 401 415 ...
     288 297 309 324 336 351 369 391 408 422 ...
     290 297 310 328 343 359 379 399 417 427 ...
     ...

.. _io-prj-file:

Projection file
============================================

The Projection file is an auxiliary optional file for proper Raster manipulation
in the right Coordinate Reference System. It is usually automatically
generated in GIS desktop application like QGIS.

Formatting rules:
- must have the ``.prj`` extension/
- must have the same name of the associated :ref:`ASCII file<io-asc-file>`;

A typical Projection file is a large single-line text that has the following structure:

.. code-block:: text

   PROJCS["SIRGAS_2000_UTM_Zone_22S",GEOGCS["GCS_SIRGAS_2000",DATUM["D_SIRGAS_2000",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",10000000.0],PARAMETER["Central_Meridian",-51.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]


.. _asc-guide:

Conversion from ``.tif`` to ``.asc``
============================================

Most GIS applications have tools for converting the commonly
distributed ``.tif`` raster files to the ``.asc`` format used in ``plans``.

Hence, users actually only have to worry about setting up the *data type*
(integer or real) and the *no-data value* in the moment of exporting
``.tif`` raster files to ``.asc`` format.

In ``QGIS 3``, users may adapt the following Python code for automating the
conversion from ``.tif`` raster files to the ``.asc`` format
(the ``.prj`` projection file is also created):

.. code-block:: python
    :linenos:

    # This code is for QGIS Python console
    import processing

    # Set file names
    input_file = 'path/to/input.tif'
    output_file = 'path/to/output.asc'

    '''
    In gdal data types are encoded in the following way:
    1: 8-bit unsigned integer (byte)
    2: 16-bit signed integer
    3: 16-bit unsigned integer
    4: 32-bit signed integer
    5: 32-bit unsigned integer
    6: 32-bit floating-point (real value)
    '''

    # Call gdal:translate
    processing.run("gdal:translate", {
       'INPUT':input_file,  # set input tif raster
       'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:4326'),  # set CRS EPSG
       'NODATA':-1,  # set no-data value
       'DATA_TYPE':6,  # 32-bit floating-point
       'FORMAT':"AAIGrid",
       'OUTPUT':output_file,  # set input tif raster
    })


Alternatively, users may use `Rasterio`_ Python library in other environments,
such as in `Colab`_ notebooks:

.. code-block:: python
    :linenos:

    # This code assumes rasterio is already installed via pip install
    import rasterio

    # Set file names
    input_file = 'path/to/input.tif'
    output_file = 'path/to/output.asc'

    # Read the input TIF file using rasterio
    with rasterio.open(input_file) as src:
        meta = src.meta.copy()  # Get metadata
        '''
        Rasterio encoded data types as in numpy (some examples):
        uint8: 8-bit unsigned integer (byte)
        int32: 32-bit signed integer
        float32: 32-bit floating-point (real value)
        '''
        # Update the metadata to change the format to ASC
        data_type = 'float32'
        meta.update({'driver': 'AAIGrid', 'dtype': data_type})
        # Open the output ASC file using rasterio
        with rasterio.open(output_file, 'w', **meta) as dst:
           # Copy the input data to the output file
           data = src.read(1) # read only the first band
           dst.write(data.astype(data_type)) # ensure data type





