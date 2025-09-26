.. file for abstracting all files

dem
===============================

``dem`` is the digital elevation model (DEM) raster file. It is a raster file representing terrain height above sea level, in meters. While not mandatory, it is a valuable input for generating many derivative files such as slope, aspect, and flow accumulation. Users often preprocess DEMs to fill depressions and interpolate missing values, ensuring a hydrologically consistent surface for further analysis.

hand
===============================

``hand`` is the Height Above Nearest Drainage (HAND). It is raster file derived from combining the DEM with a drainage network, representing the elevation difference between each pixel and its nearest stream. Values are given in meters and depend strongly on the definition of the drainage network, which can significantly influence model results. HAND can be obtained from external sources or derived directly from a DEM using geoprocessing techniques.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-dem`


twi
===============================

``twi`` is the Topographic Wetness Index (TWI), a unitless index derived from a DEM that estimates the tendency of terrain to accumulate water, assuming shallow soils and a near-surface water table. It is widely used to describe terrain-driven hydrological processes, with higher values indicating wetter conditions. Users may compute it themselves or provide it as an optional file.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-dem`
   * :ref:`io-slope`
   * :ref:`io-flowacc`


tsi
===============================

``tsi`` is the Topographic Saturation Index is a normalized, unitless index ranging from 0 to 1, representing the likelihood of saturation by combining HAND and TWI with weighted contributions. This file captures both catchment level effects and micro terrain influences, making it an important input for models simulating soil moisture and saturation dynamics.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-hand`
   * :ref:`io-twi`
   * :ref:`io-parameters_info`


ldd
===============================

``ldd`` is the Local Drain Direction (LDD), a raster file encoding the flow direction of each pixel toward its downslope neighbor, following the PC-Raster convention. It provides essential information for routing water across the landscape and is used to determine flow paths and drainage network connectivity.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-dem`
   * :ref:`io-dto`
   * :ref:`io-dist_area_hist`


hillshade
===============================

``hillshade`` is an optional raster representing shaded relief, calculated from a DEM using parameters such as solar angle and azimuth. It is primarily used for visualization and can be combined with transparency layers to enhance the perception of terrain depth.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-dem`


slope
===============================

``slope`` is an optional raster file representing the inclination of the terrain in degrees. It can be derived from the digital elevation model and is used to assess processes such as runoff and erosion. Users may provide it directly or compute it using standard geoprocessing techniques.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-dem`


soils
===============================

``soils`` is a raster file containing pixel IDs that represent soil classes. Each class is linked to an attribute table that stores parameters such as soil properties and model weights. This is a qualitative raster and is essential for encoding the land-phase hydrological characteristics used in the model.

.. warning::

   All classes encoded in the map must be listed in :ref:`io-soils_attributes`.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-soils_attributes`


soils_attributes
===============================

The ``soils_attribute`` table links soil class IDs from the soils map to their descriptive names and parameter values weights. These include model weights and other information necessary for representing soil properties in the model.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-soils`
   * :ref:`io-parameters_info`


lulc_{date}
===============================

``lulc_{date}`` is a raster file with pixel IDs encoding land use and land cover (LULC) classes for a given date. Each class links to a land use attribute table that provides descriptions and parameters used in the model, influencing processes in the land phase of the hydrological cycle.

.. warning::

   All classes encoded in the map must be listed in :ref:`io-lulc_attributes`.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-lulc_attributes`


lulc_attributes
===============================

The ``lulc_attribute`` table links land use class IDs from the LULC maps of a scenario to their names, descriptions, and parameter values weights. These attributes are used to represent vegetation, cover type, and land management effects in the model.

.. caution::

   The ``lulc_attribute`` table must live alongside map files in the respective **scenario folder** for land use. This means that different scenarios can have different encoding systems for land use.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-lulc_{date}`
   * :ref:`io-parameters_info`


climate_series
===============================

The ``climate_series`` table is a time series file containing model forcing data such as precipitation and potential evapotranspiration. It can have a time step as fine as 15 minutes, but daily or hourly series are most common. This file is required for running the model.

flowacc
===============================

``flowacc`` encodes flow accumulation, an optional raster file indicating how much water or flow would accumulate at each pixel based on upslope contributions. It may be calculated as a discrete or fuzzy surface depending on the method. Flow accumulation is often used as an input for TWI calculations.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-dem`
   * :ref:`io-twi`
   * :ref:`io-uparea`



uparea
===============================

``uparea`` is a raster file that records the exact contributing area draining into each pixel, from a single pixel up to the full catchment extent. Computing upslope area typically requires DEM preprocessing such as depression filling. This is an optional file but can improve model performance when supplied.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-flowacc`
   * :ref:`io-hand`


dto
===============================

``dto`` encodes the distance to outlet. It is a raster file computed by the model that records the flow path length from each pixel to the catchment outlet, using the `ldd` file for routing. It is an important variable for hydrograph generation, as it accounts for travel time differences across the basin.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-ldd`
   * :ref:`io-dist_area_hist`


basin
===============================

The ``basin`` file is a mandatory raster file with binary values (1 for basin pixels, 0 otherwise) defining the area of interest. Users may provide multiple basin area under the same extension. This is done by files organized in subfolders, one for each basin being modeled.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-dem`
   * :ref:`io-uparea`

dist_area_hist
===============================

The ``dist_area_hist`` intermediate table is an histogram relating flow path length (distance to outlet) to contributing area. It is generated by the model and used to compute unit hydrographs for flow routing.

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-ldd`
   * :ref:`io-dto`

parameters_info
===============================

The ``parameters_info`` table lists all model parameters and their set, lower, and upper values. These parameters represent effective, upscaled values for the catchment as a whole but can be downscaled to pixel level using weighting factors from soils, land use, and topographic saturation index. This table may also include information such as simulation time step and is useful for parameter sampling (e.g., Monte Carlo analysis).

.. admonition:: Related files
   :class: seealso
   :collapsible: closed

   * :ref:`io-lulc_attributes`
   * :ref:`io-soils_attributes`


project_info
===============================

The ``project_info`` table contains metadata describing the project, such as name, alias, source, and description. It can also list alternative parameter tables or folders to override defaults. If left empty, the model uses default project settings.


simulation_series
===============================

The ``simulation_series`` file is a table generated as output for each model run. It consolidates all simulated variables, including streamflow (observed and simulated), climate forcing data, and internal model states such as flows and storage variables. This file provides a complete record of model behavior over the simulation period and is essential for result analysis and calibration.


qobs_series
===============================

The ``qobs_series`` series is a time series table located within each basin folder, containing observed streamflow values for that catchment. Values are given as specific discharge in millimeters per time step, requiring users to convert volumetric discharge data using the catchment area at the gauge station. While optional for running the model, this file is required for calibration, validation, and performance assessment.