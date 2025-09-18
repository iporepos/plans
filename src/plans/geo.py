# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Standalone geoprocessing routines with minimal dependencies.

Overview
--------

# todo [docstring] -- overview
Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl. Pellentesque habitant morbi tristique senectus
et netus et malesuada fames ac turpis egestas.

Example
-------

# todo [docstring] -- examples
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam,
in porttitor lacus lobortis vitae. In a lacinia nisl.

.. code-block:: python

    import numpy as np
    print("Hello World!")

Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl. Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl.
"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
# import {module}
# ... {develop}

# External imports
# =======================================================================
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd

# ... {develop}

# Project-level imports
# =======================================================================
# import {module}
# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# Subsubsection example
# -----------------------------------------------------------------------
# ... {develop}

# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================


# Geometry functions
# =======================================================================


def extents_to_wkt_box(xmin, ymin, xmax, ymax):
    """
    Returns a WKT box from the given extents (xmin, ymin, xmax, ymax).

    :param xmin: Minimum x-coordinate (left)
    :type xmin: float
    :param ymin: Minimum y-coordinate (bottom)
    :type xmin: float
    :param xmax: Maximum x-coordinate (right)
    :type xmax: float
    :param ymax: Maximum y-coordinate (top)
    :type ymax: float
    :return: A string representing the box in WKT format
    :rtype: str
    """
    return f"POLYGON(({xmin} {ymin}, {xmin} {ymax}, {xmax} {ymax}, {xmax} {ymin}, {xmin} {ymin}))"


# ... {develop}


# Vector functions
# =======================================================================


def get_basins_by_gauges(
    basins,
    gauges,
    field_gauge,
    field_basin,
    field_basin_down,
    field_geometry="geometry",
    dissolve=True,
):
    """
    Retrieve a list of upstream basins for a list of gauges. This function identifies the basins in which each gauge
    is located and then finds all upstream basins for each of these basins.
    The resulting GeoDataFrame can optionally be dissolved into a single feature for each gauge.

    :param basins: A GeoDataFrame containing the basin features.
    :type basins: :class:`geopandas.GeoDataFrame`
    :param gauges: A GeoDataFrame containing the gauge locations.
    :type gauges: :class:`geopandas.GeoDataFrame`
    :param field_gauge: The name of the column in `gauges` that contains the unique identifier for each gauge.
    :type field_gauge: str
    :param field_basin: The name of the column in `basins` that contains the unique identifier for each basin.
    :type field_basin: str
    :param field_basin_down: The name of the column in `basins` that contains the unique identifier of the downstream basin.
    :type field_basin_down: str
    :param field_geometry: The name of the geometry column. Default value = "geometry"
    :type field_geometry: str
    :param dissolve: If True, dissolves the upstream basins into a single feature for each gauge. Default value = True
    :type dissolve: bool
    :return: A GeoDataFrame with the upstream basins for each gauge, including the gauge identifier. Returns None if no gauges are found within any basin.
    :rtype: :class:`geopandas.GeoDataFrame`
    """
    # ensure gauges are in the same crs
    if basins.crs != gauges.crs:
        # reproject to basin crs
        gauges = gauges.to_crs(basins.crs)

    # first get codes from basins in gauges
    gauges = gpd.sjoin(gauges, basins, how="inner", predicate="within").reset_index(
        drop=True
    )

    # check for actual join
    if len(gauges) > 0:
        # cleanup
        ls_fields = [field_gauge, field_basin, field_geometry]
        gauges = gauges[ls_fields].copy()
        print("\n")
        print(gauges)
        ls_basins = []
        for i in range(len(gauges)):
            gauge_id = gauges[field_gauge].values[i]
            basins_upstream = get_upstream_features(
                features=basins,
                field_id=field_basin,
                field_id_down=field_basin_down,
                start_id=gauges[field_basin].values[i],
                include_start=True,
                field_geometry="geometry",
            )
            if basins_upstream is not None:
                # dissolve into a single feature
                if dissolve:
                    basins_upstream = basins_upstream.dissolve()
                # append the gauge id field
                basins_upstream[field_gauge] = gauge_id
                # append to list
                ls_basins.append(basins_upstream[[field_gauge, field_geometry]].copy())
        basins_up = pd.concat(ls_basins).reset_index(drop=True)
        return basins_up
    else:
        return None


def get_upstream_features(
    features,
    field_id,
    field_id_down,
    start_id,
    include_start=True,
    field_geometry="geometry",
    is_starting=True,
):
    """
    Retrieves all upstream features from a given starting point.

    :param features: A DataFrame containing all features.
    :type features: :class:`pandas.DataFrame` or :class:`geopandas.GeoDataFrame`
    :param field_id: The name of the column containing the feature's unique ID.
    :type field_id: str
    :param field_id_down: The name of the column containing the ID of the downstream feature.
    :type field_id_down: str
    :param start_id: The ID of the starting feature.
    :type start_id: int or str
    :param include_start: [optional] Whether to include the starting feature in the output. Default value = True
    :type include_start: bool
    :param field_geometry: [optional] The name of the column containing the geometry of the feature. Default value = "geometry"
    :type field_geometry: str
    :param is_starting: [optional] A flag to indicate if it's the initial call of the function. Default value = True
    :type is_starting: bool
    :return: A DataFrame with the upstream features, or None if no upstream features are found.
    :rtype: :class:`pandas.DataFrame` or :class:`geopandas.GeoDataFrame`  or None
    """

    # assses first step condition
    if is_starting:
        # if is first step, clean up useless fields
        ls_fields = [field_id, field_id_down]
        # handle geometry field
        if field_geometry is not None:
            ls_fields.append(field_geometry)
        features = features[ls_fields].copy()
        if include_start:
            # get the starting feature
            feature_start = features[features[field_id].isin([start_id])].copy()

    # filter the upstream features
    features_up = features[features[field_id_down].isin([start_id])].copy()

    # assess halt condition
    if len(features_up) > 0:
        # setup a list for concatenation
        ls_ups = [features_up]
        # enter upstream loop
        for i in range(len(features_up)):
            # assess the local new starting point
            lcl_start_id = features_up[field_id].values[i]
            # enter recursive mode
            output = get_upstream_features(
                features=features,
                field_id=field_id,
                field_id_down=field_id_down,
                start_id=lcl_start_id,
                is_starting=False,
            )
            # handle output
            if output is not None:
                ls_ups.append(output)

        # handle to include start feature
        if is_starting and include_start:
            # include the starting feature
            ls_ups.append(feature_start)

        # concatenate all features
        features_up = pd.concat(ls_ups).reset_index(drop=True)
        return features_up
    else:
        # handle edge case for upstream feature
        if is_starting and include_start:
            return feature_start.reset_index(drop=True)
        else:
            return None


# Raster functions
# =======================================================================


def get_array_bbox(array):
    """
    Finds the bounding box for the content (1s) in a 2D pseudo-boolean array.

    :param array: 2D numpy array with values 1 (content) and 0 (background)
    :type array: :class:`numpy.ndarray`
    :return: Dictionary with keys "i_min", "i_max", "j_min", "j_max" representing the row and column bounds of the content
    :rtype: dict
    """
    # Find rows and columns containing 1's
    rows_with_content = np.where(array.sum(axis=1) > 0)[0]
    cols_with_content = np.where(array.sum(axis=0) > 0)[0]

    # If there's content, determine bounds; otherwise, return None for each bound
    if rows_with_content.size > 0 and cols_with_content.size > 0:
        i_min, i_max = rows_with_content[0], rows_with_content[-1]
        j_min, j_max = cols_with_content[0], cols_with_content[-1]
    else:
        i_min = i_max = j_min = j_max = None

    return {"i_min": i_min, "i_max": i_max, "j_min": j_min, "j_max": j_max}


# Basic processing of array values
# -----------------------------------------------------------------------


def convert(array, old_values, new_values):
    """
    Convert values in array from old to new values.

    :param array: Numpy array to convert values
    :type array: :class:`numpy.ndarray`
    :param old_values: iterable of old values
    :type old_values: :class:`numpy.ndarray`
    :param new_values: iterable of new values
    :type new_values: :class:`numpy.ndarray`
    :return: converted array
    :rtype: :class:`numpy.ndarray`
    """
    new = array * 0.0
    for i in range(len(old_values)):
        _old = old_values[i]
        _new = new_values[i]
        new = new + (_new * (array == _old))
    return new


def classify(array, upvalues, classes):
    """
    Classify array based on list of upper values and list of classes values

    :param array: numpy array to classify
    :param upvalues: 1d numpy array of upper values
    :param classes: 1d array of classes values
    :return: numpy array reclassified
    """
    new = array * 0.0
    for i in range(len(upvalues)):
        if i == 0:
            new = new + ((array <= upvalues[i]) * classes[i])
        else:
            new = new + (
                (array > upvalues[i - 1]) * (array <= upvalues[i]) * classes[i]
            )
    return new


def normalize(array, min_value=0, max_value=100):
    """
    Normalize array between min and max values

    :param array: Input array or float
    :type array: float or :class:`numpy.ndarray`
    :param min_value: minimum vale
    :type min_value: float
    :param max_value: maximum value
    :type max_value: float
    :return: Output array or float
    :rtype: :class:`numpy.ndarray`
    """
    # Find the minimum and maximum values in the original array
    old_min = np.min(array)
    old_max = np.max(array)

    # Calculate the range of the original array
    old_range = old_max - old_min
    # Calculate the range of the desired new scale
    new_range = max_value - min_value

    # Apply the normalization formula using NumPy's broadcasting capabilities
    normalized = min_value + ((array - old_min) * new_range) / old_range
    return normalized


def fuzzify(array, min_value=None, max_value=None):
    """
    Fuzzify array between min and max values with linear membership function

    :param array: Input array or float
    :type array: float or :class:`numpy.ndarray`
    :param min_value: minimum value threshold
    :type min_value: float
    :param max_value: maximum value threshold
    :type max_value: float
    :return: Output array or float
    :rtype: :class:`numpy.ndarray`
    """
    # Find the minimum and maximum values in the original array
    if min_value is None:
        min_value = np.min(array)
    if max_value is None:
        max_value = np.max(array)

    # Calculate the range of the original array
    old_range = max_value - min_value
    # Calculate the range of the desired new scale
    new_range = 1

    # Apply the normalization formula using NumPy's broadcasting capabilities
    # X_normalized = min_value + ((X - old_min) * new_range) / old_range
    fuzzified = 0.0 + ((array - min_value) * new_range) / old_range
    return fuzzified


def prune(array, min_value=None, max_value=None):
    """
    Inclusive prune values in array

    :param array: Numpy array to prune values
    :type array: :class:`numpy.ndarray`
    :param min_value: minimum values to prune (inclusive)
    :type min_value: float
    :param max_value: maximum values to prude (inclusive)
    :type max_value: float
    :return: pruned array
    :rtype: :class:`numpy.ndarray`
    """
    if min_value is not None:
        array = np.where(array < min_value, min_value, array)
    if max_value is not None:
        array = np.where(array > max_value, max_value, array)
    return array


def upscale(array, weights=None, mode="mean"):
    """
    Upscales an array using a specified mode.

    :param array: The input array to be upscaled.
    :type array: :class:`numpy.ndarray`
    :param weights: [optional] An array of weights to apply. Default value = None
    :type weights: :class:`numpy.ndarray`
    :param mode: The mode to use for upscaling, either "mean" or "sum". Default value = "mean"
    :type mode: str
    :return: The upscaled value.
    :rtype: int or float
    """
    if weights is None:
        weights = 1  # scalar 1 for broadcasting
    weighted_sum = np.sum(array * weights)
    if mode == "mean":
        return weighted_sum / np.sum(weights)
    elif mode == "sum":
        return weighted_sum
    else:
        return weighted_sum


def downscale_linear(scalar, array_covar, mode="mean"):
    """
    Applies linear downscaling to a covariance array based on a scalar value.

    :param scalar: The scalar value used for downscaling.
    :type scalar: float
    :param array_covar: The covariance array to be downscaled.
    :type array_covar: :class:`numpy.ndarray`
    :param mode: The aggregation mode to use, "mean" or "sum". Default value = "mean"
    :type mode: str
    :return: The linearly downscaled array.
    :rtype: :class:`numpy.ndarray`
    """
    funcs = {"mean": np.nanmean, "sum": np.nansum}
    return array_covar * scalar / funcs[mode](array_covar)


def downscale_variance(
    mean,
    array_covar,
    scale_factor,
    mirror=False,
    mode="simple",
    max_value=None,
    min_value=None,
):
    """
    Applies a downscaling operation to a mean array based on a covariance array and a scaling factor.

    :param mean: The input mean array.
    :type mean: :class:`numpy.ndarray`
    :param array_covar: The covariance array used for downscaling.
    :type array_covar: :class:`numpy.ndarray`
    :param scale_factor: The factor by which to downscale.
    :type scale_factor: float
    :param mirror: Whether to mirror the downscaling effect. Default value = False
    :type mirror: bool
    :param mode: The post-processing mode to apply. Can be "simple", "prune", "truncate", or "compensate". Default value = "simple"
    :type mode: str
    :param max_value: [optional] The maximum value for pruning or truncation.
    :type max_value: float
    :param min_value: [optional] The minimum value for pruning or truncation.
    :type min_value: float
    :return: The downscaled array.
    :rtype: :class:`numpy.ndarray`
    """
    # get mask
    downler = downscaling_mask(array_covar=array_covar, scale=scale_factor)

    signal = 1
    if mirror:
        signal = -1

    # compute simple scaling
    grd = mean + (signal * downler)

    # apply post-processing
    if mode == "simple" or mode is None:
        pass
    elif mode == "prune" or mode == "truncate":
        # this method does not ensure the same input mean
        grd = prune(array=grd, max_value=max_value, min_value=min_value)
    elif mode == "compensate":
        # this method fix the truncation problem
        grd_pruned = prune(array=grd, max_value=max_value, min_value=min_value)
        grd = downscale_linear(scalar=mean, array_covar=grd_pruned, mode="mean")

    return grd


# todo [refactor] -- evaluate to rename or move inside
def downscaling_mask(array_covar, scale):
    """
    Compute a downscaling mask by using a covariate array

    :param array_covar: Numpy array of a covariate
    :type array_covar: :class:`numpy.ndarray`
    :param scale: scale factor (expected to be positive)
    :type scale: float
    :return: downscaling mask array
    :rtype: :class:`numpy.ndarray`
    """
    return scale * (array_covar - np.mean(array_covar))


# Special processing of array values
# -----------------------------------------------------------------------


def soils(slope, hand, slope_threshold=25, hand_threshold=5):
    """
    Calculates a basic soil classification grid based on slope and HAND (Height Above Nearest Drainage) data.

    :param slope: The slope array.
    :type slope: :class:`numpy.ndarray`
    :param hand: The HAND (Height Above Nearest Drainage) array.
    :type hand: :class:`numpy.ndarray`
    :param slope_threshold: The slope threshold for identifying neosols. Default value = 25
    :type slope_threshold: int
    :param hand_threshold: The HAND threshold for identifying alluvial soils. Default value = 5
    :type hand_threshold: int
    :return: A grid representing soil types (1: default, 2: neosols, 3: alluvial).
    :rtype: :class:`numpy.ndarray`
    """
    # todo [develop] -- this can have more features
    grd_neosols = 1 * (slope >= slope_threshold)
    grd_alluvial = 1 * (hand <= hand_threshold)
    grd_alluvial = np.where(grd_neosols == 0, grd_alluvial, 0)
    grd_soils = (slope * 0.0) + 1
    grd_soils = grd_soils + (2 * grd_neosols) + (1 * grd_alluvial)
    return grd_soils


def slope(dem, cellsize, degree=True):
    """
    Calculate slope using gradient-based algorithms on a 2D numpy array.

    :param dem: 2D numpy array representing the Digital Elevation Model (``DEM``).
    :type dem: :class:`numpy.ndarray`
    :param cellsize: The size of a grid cell in the ``DEM`` (both in x and y directions).
    :type cellsize: float
    :param degree: If True (default), the output slope values are in degrees. If False, output units are in radians.
    :type degree: bool
    :return: numpy array representing the slope values.
    :rtype: :class:`numpy.ndarray`
    """
    grad = np.gradient(dem)
    gradx = grad[0] / cellsize
    grady = grad[1] / cellsize
    gradv = np.sqrt((gradx * gradx) + (grady * grady))
    slope_array = np.arctan(gradv)
    if degree:
        slope_array = slope_array * 360 / (2 * np.pi)
    return slope_array


def buffer(grd_input, n_radius):
    """
    Calculate a buffer mask

    :param grd_input: Pseudo-boolean 2D numpy array where pixels with value 1 represent the foreground.
    :type grd_input: :class:`numpy.ndarray`
    :param n_radius: number of pixels for buffer (inclusive)
    :type n_radius: int
    :return: Pseudo-boolean 2D numpy array representing buffer area.
    :rtype: :class:`numpy.ndarray`
    """
    grd_distance = euclidean_distance(grd_input)
    grd_buffer = np.where(grd_distance <= n_radius, 1, 0)
    return grd_buffer


def euclidean_distance(grd_input):
    """
    Calculate the Euclidean distance from pixels with value 1.

    :param grd_input: Pseudo-boolean 2D numpy array where pixels with value 1 represent the foreground.
    :type grd_input: :class:`numpy.ndarray`
    :return: 2D numpy array representing the Euclidean distance.
    :rtype: :class:`numpy.ndarray`

    **Note**

    - The function uses the `distance_transform_edt` from `scipy.ndimage` to compute the Euclidean distance.
    - The inputs array is treated as a binary mask, and the distance is calculated from foreground pixels (value 1).

    """
    from scipy.ndimage import distance_transform_edt

    grd_input = 1 * (grd_input == 0)  # reverse foreground values
    # Calculate the distance map
    return distance_transform_edt(grd_input)


def twi(slope, flowacc, cellsize):
    """
    Calculate the Topographic Wetness Index ``TWI``.

    :param slope: 2D numpy array representing the slope in degrees.
    :type slope: :class:`numpy.ndarray`
    :param flowacc: 2D numpy array representing the flow accumulation.
    :type flowacc: :class:`numpy.ndarray`
    :param cellsize: The size of a grid cell (delta x = delta y).
    :type cellsize: float
    :return: 2D numpy array representing the Topographic Wetness Index.
    :rtype: :class:`numpy.ndarray`

    **Note**

    - The function uses the formula: TWI = ln( A / hc_colors tan(S)), where A is flow accumulation, hc_colors is the cell resolution and S is slope in radians.
    - The inputs arrays `slope` and `flowacc` should have the same dimensions.
    - The formula includes a small value (0.01) to prevent issues with tangent calculations for non-NaN values.

    """
    # +0.01 is a hack for non-nan values
    return np.log((flowacc / cellsize) / (np.tan((slope * np.pi / 180) + 0.01)))


def shalstab_wetness(
    flowacc,
    slope,
    cellsize,
    soil_phi,
    soil_z,
    soil_c,
    soil_p,
    water_p=997,
    g=9.8,
    degree=True,
    kPa=True,
):
    """
    Calculate the SHALSTAB wetness model

    :param flowacc: flow accumulation map (square meters)
    :type flowacc: :class:`numpy.ndarray`
    :param slope: slope map (degrees or radians)
    :type slope: :class:`numpy.ndarray`
    :param cellsize: grid cell size (meters)
    :type cellsize: float
    :param soil_phi: soil angle of internal friction (degrees or radians)
    :type soil_phi: :class:`numpy.ndarray` or float
    :param soil_z: soil depth (meters)
    :type soil_z: :class:`numpy.ndarray` or float
    :param soil_c: soil cohesion (Pa or N/m0² or kg/ms²)
    :type soil_c: :class:`numpy.ndarray` or float
    :param soil_p: soil density (kg/m0³)
    :type soil_p: :class:`numpy.ndarray` or float
    :param water_p: water density (kg/m0³)
    :type water_p: float
    :param g: gravity acceleration (m0 / s²)
    :type g: float
    :param degree: flag to note if slope and soil_phi are in degrees
    :type degree: bool
    :param kPa: flag to note if soil_c in kPa
    :type kPa: bool
    :return: map of q/T ratio
    :rtype: :class:`numpy.ndarray`
    """

    if degree:
        # convert to radians
        slope = np.radians(slope)
        soil_phi = np.radians(soil_phi)

    if kPa:
        # convert to Pa
        soil_c = soil_c * 1000

    # get density ratio
    density_r = soil_p / water_p

    # get tangent ratio
    tan_r = 1 - (np.tan(slope) / np.tan(soil_phi))

    slope_term = density_r * tan_r

    # get force term
    cohesion_term = soil_c / (
        np.square(np.cos(slope)) * np.tan(soil_phi) * water_p * g * soil_z
    )

    topo_term = cellsize * np.sin(slope) / flowacc

    # apply full equation
    q_t = topo_term * (slope_term + cohesion_term)

    # force non-negative
    q_t = q_t * (q_t > 0) + 0.0001

    shalstab_classes = classify(
        array=np.log10(q_t),
        upvalues=np.array([-3.1, -2.8, -2.5, -2.2, 10]),
        classes=np.array([6, 5, 4, 3, 2]),
    )

    # improve id 1 and id 7
    mask1 = 1 * (np.tan(slope) <= np.tan(soil_phi) * (1 - (1 / density_r)))
    mask7 = 1 * (np.tan(soil_phi) > np.tan(slope))

    # shalstab_classes = (shalstab_classes * (mask1 != 1)) + mask1
    # shalstab_classes = (shalstab_classes * (mask7 != 1)) + (mask7 * 7)

    return q_t, shalstab_classes


def usle_l(slope, cellsize):
    """
    Wischmeier & Smith (1978) L factor

    L = (x / 22.13) ^ m0

    where:

    m0 = 0.2 when sinθ < 0.01;
    m0 = 0.3 when 0.01 ≤ sinθ ≤ 0.03;
    m0 = 0.4 when 0.03 < sinθ < 0.05;
    m0 = 0.5 when sinθ ≥ 0.05

    x is the plot lenght taken as 1.4142 * cellsize  (diagonal length of cell)

    :param slope: slope in degrees of terrain 2d array
    :type slope: :class:`numpy.ndarray`
    :param cellsize: cell size in meters
    :type cellsize: float
    :return: Wischmeier & Smith (1978) L factor 2d array
    :rtype: :class:`numpy.ndarray`
    """
    slope_rad = np.pi * 2 * slope / 360
    lcl_grad = np.sin(slope_rad)
    m = classify(
        lcl_grad,
        upvalues=(0.01, 0.03, 0.05, np.max(lcl_grad)),
        classes=(0.2, 0.3, 0.4, 0.5),
    )
    return np.power(np.sqrt(2) * cellsize / 22.13, m)


def usle_s(slope):
    """
    Calculates the USLE S-factor (slope steepness factor) based on the Wischmeier & Smith (1978) equation.

    S = 65.41(sinθ)^2 + 4.56sinθ + 0.065

    :param slope: Slope in degrees of terrain.
    :type slope: :class:`numpy.ndarray`
    :return: The USLE S-factor.
    :rtype: :class:`numpy.ndarray`
    """
    slope_rad = np.pi * 2 * slope / 360
    lcl_grad = np.sin(slope_rad)
    return (65.41 * np.power(lcl_grad, 2)) + (4.56 * lcl_grad) + 0.065


def usle_m_a(q, prec, r, k, l, s, c, p, cellsize=30):
    """
    USLE-M Annual Soil Loss (Kinnell & Risse, 1998)

    :param q: Annual runoff in mm/year.
    :type q: :class:`numpy.ndarray`
    :param prec: Annual precipitation in mm/year.
    :type prec: :class:`numpy.ndarray` or float
    :param r: Rain erosivity in MJ mm h-1 ha-1 year-1.
    :type r: :class:`numpy.ndarray` or float
    :param k: Erodibility K factor in ton h MJ-1 mm-1.
    :type k: :class:`numpy.ndarray` or float
    :param l: USLE/RUSLE L factor.
    :type l: :class:`numpy.ndarray` or float
    :param s: USLE/RUSLE S factor.
    :type s: :class:`numpy.ndarray` or float
    :param c: C_UM factor.
    :type c: :class:`numpy.ndarray` or float
    :param p: USLE/RUSLE P factor.
    :type p: :class:`numpy.ndarray` or float
    :param cellsize: Grid cell size in meters. Default value = 30
    :type cellsize: float
    :return: Annual Soil Loss in ton/year.
    :rtype: :class:`numpy.ndarray`
    """
    return (q / prec) * r * k * l * s * c * p * (cellsize * cellsize / (100 * 100))


def rivers_wedge(grd_rivers, wedge_width=3, wedge_depth=3):
    """
    Generate a wedge-like trench along the river lines.

    Notes:

    - The function generates a wedge-like trench along the river lines based on distance transform.
    - The inputs array `grd_rivers` should be a pseudo-boolean grid where rivers are represented as 1 and others as 0.
    - The width `w` controls the width of the trench, and `h` controls its height.

    :param grd_rivers: Pseudo-boolean grid indicating the presence of rivers.
    :type grd_rivers: :class:`numpy.ndarray`
    :param wedge_width: Width (single-sided) in pixels. Default is 3.
    :type wedge_width: int
    :param wedge_depth: Depth in meters. Default is 3.
    :type wedge_depth: float
    :return: Grid of the wedge (positive).
    :rtype: :class:`numpy.ndarray`

    """
    grd_dist = euclidean_distance(grd_input=grd_rivers)
    return (((-wedge_depth / wedge_width) * grd_dist) + wedge_depth) * (
        grd_dist <= wedge_width
    )


def carve_dem(grd_dem, grd_rivers, wedge_width=3, wedge_depth=10):
    """
    Burn a ``DEM`` map with river lines.

    :param grd_dem: ``DEM`` map.
    :type grd_dem: :class:`numpy.ndarray`
    :param grd_rivers: River map (pseudo-boolean).
    :type grd_rivers: :class:`numpy.ndarray`
    :param wedge_width: Width parameter in cells. Default is 3.
    :type wedge_width: int
    :param wedge_depth: Depth parameter. Default is 10.
    :type wedge_depth: float
    :return: Burned ``DEM``.
    :rtype: :class:`numpy.ndarray`

    **Note**

    - The function burns a ``DEM`` map with river lines, creating a wedge-like trench along the rivers.
    - The inputs array `grd_rivers` should be a pseudo-boolean grid where rivers are represented as 1 and others as 0.
    - The width `w` controls the width of the trench, and `h` controls its height.

    """
    grd_wedge = rivers_wedge(
        grd_rivers, wedge_width=wedge_width, wedge_depth=wedge_depth
    )
    return (grd_dem + wedge_depth) - grd_wedge


def downstream_coordinates(n_dir, i, j, s_convention="ldd"):
    """
    Compute i and j downstream cell coordinates based on cell flow direction.

    :param n_dir: Flow direction code.
    :type n_dir: int
    :param i: i (row) array index.
    :type i: int
    :param j: j (column) array index.
    :type j: int
    :param s_convention: String of flow direction convention. Options: 'ldd' and 'd8'. Default is 'ldd'.
    :type s_convention: str
    :return: Dictionary of downstream i, j, and distance factor.
    :rtype: dict

    **Notes**

    - Assumes a specific flow direction convention ('ldd' or 'd8').
    - The output dictionary contains keys 'i', 'j', and 'distance'.
    - The 'i' and 'j' values represent downstream cell coordinates.
    - The 'distance' value is the Euclidean distance to the downstream cell.

    **Examples**

    >>> downstream_coordinates(n_dir=1, i=3, j=4, s_convention='ldd')
    {'i': 4, 'j': 3, 'distance': np.float64(1.4142135623730951)}

    Change convention:

    >>> downstream_coordinates(n_dir=5, i=10, j=15, s_convention='d8')
    {'i': 10, 'j': 14, 'distance': np.float64(1.0)}

    """
    # directions dictionaries
    dct_dirs = {
        "ldd": {
            "1": {"di": 1, "dj": -1},
            "2": {"di": 1, "dj": 0},
            "3": {"di": 1, "dj": 1},
            "4": {"di": 0, "dj": -1},
            "5": {"di": 0, "dj": 0},
            "6": {"di": 0, "dj": 1},
            "7": {"di": -1, "dj": -1},
            "8": {"di": -1, "dj": 0},
            "9": {"di": -1, "dj": 1},
        },
        "d8": {
            "0": {"di": 0, "dj": 0},
            "1": {"di": 0, "dj": 1},
            "2": {"di": -1, "dj": 1},
            "3": {"di": -1, "dj": 0},
            "4": {"di": -1, "dj": -1},
            "5": {"di": 0, "dj": -1},
            "6": {"di": 1, "dj": -1},
            "7": {"di": 1, "dj": 0},
            "8": {"di": 1, "dj": 1},
        },
    }
    # set dir dict
    dct_dir = dct_dirs[s_convention.lower()]
    di = dct_dir[str(n_dir)]["di"]
    dj = dct_dir[str(n_dir)]["dj"]
    dist = np.sqrt(np.power(di, 2) + np.power(dj, 2))
    dct_output = {"i": i + di, "j": j + dj, "distance": dist}
    return dct_output


def distance_to_outlet(grd_ldd, n_res=30, s_convention="ldd"):
    """
    Compute the distance to outlet ``DTO`` raster of a given basin.

    :param grd_ldd: 2d numpy array of flow direction LDD
    :type grd_ldd: :class:`numpy.ndarray`
    :param n_res: Resolution factor for the output distance raster. Default is 30.
    :type n_res: int
    :param s_convention: String of flow direction convention. Options: 'ldd' and 'd8'. Default is 'ldd'.
    :type s_convention: str
    :return: 2d numpy array distance
    :rtype: :class:`numpy.ndarray`

    Notes:

    - The distance is set to 0 outside the basin area.

    """

    def is_offgrid(i, j):
        if i < 0:
            return True
        elif i >= n_rows:
            return True
        elif j < 0:
            return True
        elif j >= n_cols:
            return True
        else:
            return False

    def is_center(ldd):
        # halt
        dict_halt = {"ldd": 5, "d8": 0}
        if ldd == dict_halt[s_convention]:
            return True
        else:
            return False

    # compute total number of cells:
    n_total = grd_ldd.size
    # deploy out distance raster
    grd_outdist = -1 * np.ones(shape=np.shape(grd_ldd), dtype="float32")
    # set loop parameters
    n_rows = np.shape(grd_ldd)[0]
    n_cols = np.shape(grd_ldd)[1]
    n_counter = 0
    for i in range(n_rows):
        for j in range(n_cols):
            # initiate cell loop:
            i_current = i
            j_current = j
            # first check: if outdist is already set
            lcl_outdist = grd_outdist[i_current][j_current]
            # not set:
            if lcl_outdist == -1:
                lcl_ldd = grd_ldd[i_current][j_current]
                # set queues
                list_accdist = list()
                list_traced_is = list()
                list_traced_js = list()
                # trace loop
                n_trace_count = 0
                while True:
                    # get downstream position
                    dct_out = downstream_coordinates(
                        n_dir=lcl_ldd,
                        i=i_current,
                        j=j_current,
                        s_convention=s_convention,
                    )
                    i_next = dct_out["i"]
                    j_next = dct_out["j"]
                    n_dist = dct_out["distance"]
                    # append to queue
                    if n_trace_count == 0:
                        list_accdist.append(n_dist)
                    else:
                        list_accdist.append(n_dist + list_accdist[n_trace_count - 1])
                    list_traced_is.append(i_current)
                    list_traced_js.append(j_current)
                    # halting options
                    b_off = is_offgrid(i=i_next, j=j_next)
                    b_center = is_center(ldd=lcl_ldd)
                    if b_off or b_center:
                        # QUIT
                        n_traced_outdist = 0
                        break
                    # check if next cell is a mapped path
                    n_next_outdist = grd_outdist[i_next][j_next]
                    if n_next_outdist == -1:
                        # MOVE
                        i_current = i_next
                        j_current = j_next
                        # update flowdir
                        lcl_ldd = grd_ldd[i_current][j_current]
                        n_trace_count = n_trace_count + 1
                    else:
                        # QUIT
                        n_traced_outdist = n_next_outdist
                        break
                # now manipulate queues
                vct_accdist = np.array(list_accdist)
                vct_accdist_inv = vct_accdist[::-1]
                vct_is = np.array(list_traced_is)
                vct_js = np.array(list_traced_js)
                # get outdist path
                vct_outdist = vct_accdist_inv + n_traced_outdist
                # burn loop
                for k in range(len(vct_outdist)):
                    grd_outdist[vct_is[k]][vct_js[k]] = vct_outdist[k]
            else:
                pass
    return n_res * grd_outdist
