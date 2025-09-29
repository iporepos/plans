.. file for abstracting all files

.. WARNING bug happens if separators ==== are different size

dem
============================================================

Digital elevation model (DEM) raster file. It is a raster file representing terrain height above sea level, in meters. While not mandatory, it is a valuable input for generating many derivative files such as slope, aspect, and flow accumulation. Users often preprocess DEMs to fill depressions and interpolate missing values, ensuring a hydrologically consistent surface for further analysis.

hand
============================================================

A raster file derived from combining the DEM with a drainage network, representing the elevation difference between each pixel and its nearest stream. Values are given in meters and depend strongly on the definition of the drainage network, which can significantly influence model results. HAND can be obtained from external sources or derived directly from a DEM using geoprocessing techniques.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-dem`


twi
============================================================

A unitless index map derived from a DEM that estimates the tendency of terrain to accumulate water, assuming shallow soils and a near-surface water table. It is widely used to describe terrain-driven hydrological processes, with higher values indicating wetter conditions. Users may compute it themselves or provide it as an optional file.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-dem`
   * :ref:`io-slope`
   * :ref:`io-flowacc`


tsi
============================================================

A normalized, unitless index map ranging from 0 to 1, representing the likelihood of saturation by combining HAND and TWI with weighted contributions. This file captures both catchment level effects and micro terrain influences, making it an important input for models simulating soil moisture and saturation dynamics.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-hand`
   * :ref:`io-twi`
   * :ref:`io-parameters_info`


ldd
============================================================

Local Drain Direction (LDD), a raster file encoding the flow direction of each pixel toward its downslope neighbor, following the `WhiteboxTool <https://www.whiteboxgeo.com/>`_ convention. It provides essential information for routing water across the landscape and is used to determine flow paths and drainage network connectivity.

.. admonition:: LDD standard convention
   :class: warning

   ``plans`` follows the ``wbt`` convention derived from the `WhiteboxTool <https://www.whiteboxgeo.com/>`_:

   .. csv-table:: ``wbt`` convention
      :width: 30%

      64, 128, 1
      32, 0, 2
      16, 8, 4

   Users may need to transform their own LDD map to match this convention.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-dem`
   * :ref:`io-dto`
   * :ref:`io-dist_area_hist`


hillshade
============================================================

A raster representing shaded relief, calculated from a DEM using parameters such as solar angle and azimuth. It is primarily used for visualization and can be combined with transparency layers to enhance the perception of terrain depth.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-dem`


slope
============================================================

A raster file representing the inclination of the terrain in degrees. It can be derived from the digital elevation model and is used to assess processes such as runoff and erosion. Users may provide it directly or compute it using standard geoprocessing techniques.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-dem`


soils
============================================================

A raster file containing pixel IDs that represent soil classes. Each class is linked to an attribute table that stores parameters such as soil properties and model weights. This is a qualitative raster and is essential for encoding the land-phase hydrological characteristics used in the model.

.. warning::

   All classes encoded in the map must be listed in :ref:`io-soils_attributes`.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-soils_attributes`


soils_attributes
============================================================

A table that links soil class IDs from the soils map to their descriptive names and parameter values weights. These include model weights and other information necessary for representing soil properties in the model.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-soils`
   * :ref:`io-parameters_info`

soils_{parameter}
============================================================

This files are intermediate maps of parameters related to soils. For all parameters related to soils, a map is generated considering the downscaling weights provided in  :ref:`io-soils_attributes`.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-soils`
   * :ref:`io-soils_attributes`
   * :ref:`io-parameters_info`


lulc_{date}
============================================================

A raster map with pixel IDs encoding land use and land cover (LULC) classes for a given date. Each class links to a land use attribute table that provides descriptions and parameters used in the model, influencing processes in the land phase of the hydrological cycle.

.. warning::

   All classes encoded in the map must be listed in :ref:`io-lulc_attributes`.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-lulc_attributes`


lulc_attributes
============================================================

A table that links land use class IDs from the LULC maps of a scenario to their names, descriptions, and parameter values weights. These attributes are used to represent vegetation, cover type, and land management effects in the model.

.. caution::

   This table must live alongside map files in the respective **scenario folder** for land use. This means that different scenarios can have different encoding systems for land use.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-lulc_{date}`
   * :ref:`io-parameters_info`


lulc_{date}_{parameter}
============================================================

This files are intermediate maps of parameters related to Land Use. For all parameters related to land use, and for all land use maps available for a given scenario, a map is generated considering the downscaling weights provided in  :ref:`io-lulc_attributes`.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-lulc_{date}`
   * :ref:`io-lulc_attributes`
   * :ref:`io-parameters_info`


lulc_series
=============================================================

This time series is an intermediate table that relates all land use maps in a given scenario with an ID field.


climate_series
=============================================================

A time series file containing model forcing data such as precipitation and potential evapotranspiration. It can have a time step as fine as 15 minutes, but daily or hourly series are most common. This file is required for running the model.


climate_{lulc-scenario}_lulc_series
=============================================================

This time series is a merger or :ref:`io-climate_series` and :ref:`io-lulc_series` for a given Land Use scenario. It relates all time steps for a given climate series to a land use map and related parameters at a given Land Use scenario.

.. important::

   When generated, this time series downscale climate variables to the simulation time step defined in :ref:`io-parameters_info`.
   Hence, it can be a heavy file.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-climate_series`
   * :ref:`io-lulc_series`
   * :ref:`io-parameters_info`



flowacc
=============================================================

A raster map indicating unitary accumulated water at each pixel based on upslope contributions. It may be calculated as a discrete or fuzzy surface depending on the method. Flow accumulation is often used as an input for TWI calculations.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-dem`
   * :ref:`io-twi`
   * :ref:`io-uparea`



uparea
=============================================================

A raster file that records the exact contributing area draining into each pixel, from a single pixel up to the full catchment extent. Computing upslope area typically requires DEM preprocessing such as depression filling. This is an optional file but can improve model performance when supplied.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-flowacc`
   * :ref:`io-hand`



dto
=============================================================

A raster map encoding distance to basin outlet. It is a raster file computed by the model that records the flow path length from each pixel to the catchment outlet, using LDD information for routing. It is an important variable for hydrograph generation, as it accounts for travel time differences across the basin.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-ldd`
   * :ref:`io-dist_area_hist`



basin
=============================================================

A mandatory raster file with binary values (1 for basin pixels, 0 otherwise) defining the basin/catchment of interest. Users may provide multiple basin area under the same extension. This is done by files organized in subfolders, one for each basin being modeled.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-dem`
   * :ref:`io-uparea`



dist_area_hist
=============================================================

A histogram relating flow path length (distance to outlet) to contributing/upslope area. It is generated by the model and used to compute unit hydrographs for flow routing.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-ldd`
   * :ref:`io-dto`



parameters_info
=============================================================

Table that lists all model parameters and their set, lower, and upper values. These parameters represent effective, upscaled values for the basin as a whole but can be downscaled to pixel level using weighting factors from soils, land use, and topographic saturation index. This table may also include information such as simulation time step and is useful for parameter sampling (e.g., Monte Carlo analysis).

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-lulc_attributes`
   * :ref:`io-soils_attributes`



project_info
=============================================================

A table that contains metadata describing the project, such as name, alias, source, and description.


simulation_series
=============================================================

A time series table generated as output for each model run. It consolidates all simulated variables, including streamflow (observed and simulated), climate forcing data, and internal model states such as flows and storage variables. This file provides a complete record of model behavior over the simulation period and is essential for result analysis and calibration.


qobs_series
=============================================================

A time series table located within each basin folder, containing observed streamflow values for that catchment. While optional for running the model, this file is required for calibration, validation, and performance assessment.

.. warning::

   Values for streamflow must be given as **specific discharge** in millimeters per time step, requiring users to convert volumetric discharge data using the catchment area at the gauge station.