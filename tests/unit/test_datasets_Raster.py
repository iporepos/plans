"""
Unit tests for the Raster family, on small grids in memory.

Assertions in plain words:

* ``Raster`` is a ``GeoUnivar``, and its grid stays a grid.
* Methods of the family work on the values of the grid, without missing data.
* Statistics follow the grid, after masks and after edits in place.
* The view is the one of ``GeoUnivar``, with the raster on the map panel, in map coordinates.
* Both color schemes work, with continuous as the default.
* The helper geometry is in map coordinates, and is seen on the map.
* ``QualiRaster`` shows the map and the areas, and refuses meaningless statistics.
* Metadata, AOI and zonal methods work on integer grids without masked cells.

"""

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import os
import tempfile
import unittest

# ... {develop}

# External imports
# =======================================================================
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import rasterio

# ... {develop}

# Project-level imports
# =======================================================================
from plans import viewer
from plans.datasets.analyst import GeoUnivar, Univar
from plans.datasets.core import QualiRaster, RasterCollection, SciRaster, Zones
from plans.datasets.spatial import AOI, Elevation

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

METADATA = {
    "ncols": 10,
    "nrows": 8,
    "xllcorner": 1000.0,
    "yllcorner": 2000.0,
    "cellsize": 30.0,
    "NODATA_value": -99999,
    "crs": None,
    "transform": None,
}

# ... {develop}

# FUNCTIONS
# ***********************************************************************


class FakeCRS:
    """
    A CRS, without the need of the database of PROJ.
    """

    def __init__(self, epsg=31982, is_geographic=False, linear_units="metre", wkt=""):
        self.epsg = epsg
        self.is_geographic = is_geographic
        self.is_projected = not is_geographic
        self.linear_units = linear_units
        self.wkt = wkt

    def to_epsg(self):
        return self.epsg

    def to_wkt(self):
        return self.wkt


def get_sci(cls=SciRaster):
    """
    Get a scientific raster with one missing cell, with values from 0 to 79.
    """
    grid = np.arange(80.0).reshape(8, 10)
    grid[0, 0] = np.nan
    rst = cls()
    rst.set_raster_metadata(metadata=METADATA)
    rst.set_data(grid=grid)
    rst.update()
    return rst


def get_quali(grid=None, cls=QualiRaster):
    """
    Get a qualitative raster with two classes, without masked cells by default.
    """
    if grid is None:
        grid = np.ones(shape=(8, 10), dtype="uint8")
        grid[:, 5:] = 2
    rst = cls()
    rst.set_raster_metadata(metadata=METADATA)
    # a CRS in meters, as read by areas
    rst.raster_metadata["crs"] = FakeCRS()
    rst.set_data(grid=grid)
    rst.update()
    rst.set_table(
        dataframe=pd.DataFrame(
            {
                "id": [1, 2],
                "name": ["Forest", "Water"],
                "alias": ["F", "W"],
                "color": ["green", "blue"],
            }
        )
    )
    return rst


def get_fig(rst):
    fig = rst.view(show=False, return_fig=True)
    fig.canvas.draw()
    return fig


# CLASSES
# ***********************************************************************


class TestRasterFamily(unittest.TestCase):

    def tearDown(self):
        plt.close("all")

    def test_chain(self):
        rst = get_sci()
        self.assertIsInstance(rst, GeoUnivar)
        self.assertIsInstance(rst, Univar)
        self.assertEqual(rst.data.shape, (8, 10))
        self.assertEqual(rst.size, 80)
        self.assertEqual(rst.varname, "Unknown variable")

    def test_getters(self):
        rst = get_sci()
        vct = rst.get_grid_data()
        self.assertEqual(len(vct), 79)
        self.assertEqual(rst.var_min, 1)
        self.assertEqual(rst.var_max, 79)
        self.assertEqual(
            rst.stats_df.query("statistic == 'count'")["value"].iloc[0], 79
        )
        self.assertEqual(len(rst.get_cdf_weibull()), 79)
        for getter in [rst.get_normality, rst.get_frequency, rst.get_cdf_gumbel]:
            with self.subTest(getter=getter.__name__):
                self.assertIsNotNone(getter())

    def test_same_stats_as_univar(self):
        rst = get_sci()
        uv = Univar()
        uv.set_array(array=rst.get_grid_data())
        pd.testing.assert_frame_equal(rst.get_stats_df(), uv.stats_df)

    def test_stats_follow_the_grid(self):
        rst = get_sci()
        self.assertEqual(rst.get_stats()["max"], 79)
        self.assertEqual(rst.stats_df.query("statistic == 'max'")["value"].iloc[0], 79)

        # a mask, and its release
        grid_aoi = np.ones(shape=(8, 10))
        grid_aoi[-1, :] = 0
        rst.apply_aoi_mask(grid_aoi=grid_aoi)
        self.assertEqual(rst.stats_df.query("statistic == 'max'")["value"].iloc[0], 69)
        self.assertEqual(rst.var_max, 69)
        self.assertEqual(rst.get_stats()["max"], 69)
        rst.release_aoi_mask()
        self.assertEqual(rst.get_stats()["max"], 79)

        # an edit in place
        rst.data[1, 1] = 1000.0
        self.assertEqual(rst.get_stats()["max"], 1000)

    def test_view_follows_edit_in_place(self):
        rst = get_sci()
        vct_old = rst.stats_df
        rst.data[1, 1] = 1000.0
        fig = get_fig(rst)
        self.assertIsNot(rst.stats_df, vct_old)
        self.assertEqual(
            rst.stats_df.query("statistic == 'max'")["value"].iloc[0], 1000
        )
        plt.close(fig)

    def test_view_panels(self):
        rst = get_sci()
        for layout in ["full", "mini"]:
            with self.subTest(layout=layout):
                rst.view_specs["layout"] = layout
                fig = get_fig(rst)
                ax_map, ax_data, ax_hist, ax_cdf, ax_cbar = fig.get_axes()
                # square panel, in line with the others
                box_map = ax_map.get_window_extent()
                self.assertAlmostEqual(box_map.width, box_map.height, places=3)
                self.assertAlmostEqual(
                    box_map.y1, ax_data.get_window_extent().y1, places=3
                )
                # the raster in map coordinates
                self.assertEqual(len(ax_map.images), 1)
                self.assertEqual(
                    list(ax_map.images[0].get_extent()), [1000, 1300, 2000, 2240]
                )
                self.assertLessEqual(ax_map.get_xlim()[0], 1000)
                self.assertGreaterEqual(ax_map.get_xlim()[1], 1300)
                self.assertEqual(ax_map.images[0].get_array().shape, (8, 10))
                # the bar shares the y axis of the panels, grid above the raster
                np.testing.assert_allclose(ax_cbar.get_ylim(), ax_hist.get_ylim())
                ls_grids = [a for a in ax_map.artists if isinstance(a, viewer.AxisGrid)]
                self.assertEqual(len(ls_grids), 2)
                self.assertLess(ax_map.images[0].get_zorder(), ls_grids[0].get_zorder())
                self.assertGreater(ax_map.xaxis.get_zorder(), ls_grids[0].get_zorder())
                self.assertEqual(len(ax_map.get_xticks()), 3)
                # hist and CDF with the same width
                self.assertAlmostEqual(
                    ax_hist.get_position().width, ax_cdf.get_position().width
                )
                plt.close(fig)

    def test_color_schemes(self):
        rst = get_sci()
        self.assertEqual(rst.view_specs["scheme_cmap"], "continuous")
        rst.view_specs["range"] = [0, 100]
        fig = get_fig(rst)
        ax_map = fig.get_axes()[0]
        norm = ax_map.images[0].norm
        self.assertIsInstance(norm, mcolors.Normalize)
        self.assertNotIsInstance(norm, mcolors.BoundaryNorm)
        self.assertEqual((norm.vmin, norm.vmax), (0, 100))
        np.testing.assert_allclose(fig.get_axes()[4].get_ylim(), [0, 100])
        plt.close(fig)

        # classes as in GeoUnivar
        rst.view_specs["scheme_cmap"] = "equal"
        rst.view_specs["n_classes_cmap"] = 4
        fig = get_fig(rst)
        ax_map = fig.get_axes()[0]
        self.assertIsInstance(ax_map.images[0].norm, mcolors.BoundaryNorm)
        self.assertEqual(len(fig.get_axes()[4].get_yticks()), 5)
        plt.close(fig)

    def test_classes_fill_the_range(self):
        rst = get_sci()
        rst.view_specs["scheme_cmap"] = "equal"
        rst.view_specs["n_classes_cmap"] = 4
        # boundaries at 20.5, 40 and 59.5. The last one is too close to the end
        rst.view_specs["range"] = [10, 60]
        fig = get_fig(rst)
        vct_bounds = fig.get_axes()[0].images[0].norm.boundaries
        np.testing.assert_allclose(vct_bounds, [10, 20.5, 40, 60])
        np.testing.assert_allclose(fig.get_axes()[4].get_ylim(), [10, 60])
        plt.close(fig)

    def test_crs_info(self):
        # CRS and what is expected
        ls_cases = [
            (FakeCRS(), {"epsg": 31982, "units": "m"}),
            (
                FakeCRS(epsg=4674, is_geographic=True, linear_units="unknown"),
                {"epsg": 4674, "units": "deg."},
            ),
            # without the database of PROJ
            (
                FakeCRS(
                    epsg=None,
                    linear_units="unknown",
                    wkt='LOCAL_CS["A",UNIT["metre",1]]',
                ),
                {"epsg": None, "units": "m"},
            ),
            (
                FakeCRS(
                    epsg=None,
                    linear_units="unknown",
                    wkt='LOCAL_CS["A",UNIT["degree",1]]',
                ),
                {"epsg": None, "units": "deg."},
            ),
            (None, {"epsg": None, "units": None}),
        ]
        for crs, dc_expected in ls_cases:
            with self.subTest(dc_expected=dc_expected):
                rst = get_sci()
                rst.raster_metadata["crs"] = crs
                self.assertEqual(rst.get_crs_info(), dc_expected)

    def test_metadata_lines(self):
        rst = get_sci()
        rst.raster_metadata["crs"] = FakeCRS()
        ls_lines = rst.get_metadata_lines()
        self.assertIn(" Cell: 30 m", ls_lines)
        self.assertIn(" EPSG: 31982", ls_lines)
        # degrees keep their small cells
        rst.raster_metadata["crs"] = FakeCRS(
            epsg=4674, is_geographic=True, linear_units=""
        )
        rst.set_raster_metadata(metadata={"cellsize": 0.000277778})
        self.assertIn(" Cell: 0.000277778 deg.", rst.get_metadata_lines())
        # nothing known
        rst.raster_metadata["crs"] = None
        rst.raster_metadata["NODATA_value"] = None
        ls_lines = rst.get_metadata_lines()
        self.assertIn(" EPSG: n/a", ls_lines)
        self.assertIn("  NaN: n/a", ls_lines)

    def test_annotations_place(self):
        for rst, n_columns in [(get_sci(), 3), (get_quali(), 1)]:
            with self.subTest(cls=type(rst).__name__):
                fig = get_fig(rst)
                ax_map = fig.get_axes()[0]
                box_map = ax_map.get_window_extent()
                # all but the title
                ls_notes = [t for t in fig.texts if ":" in t.get_text()]
                self.assertEqual(
                    len({t.get_position()[0] for t in ls_notes}), n_columns
                )
                for t in ls_notes:
                    box = t.get_window_extent()
                    self.assertGreaterEqual(box.y0, box_map.y0)
                    self.assertGreater(box.x0, box_map.x1)
                    self.assertLessEqual(box.x1, fig.bbox.width)
                # below the last lateral panel, with its labels
                ax_above = fig.get_axes()[rst.view_specs["ax_hist"]]
                n_top = ax_above.get_tightbbox().y0
                self.assertLessEqual(
                    max(t.get_window_extent().y1 for t in ls_notes), n_top
                )
                plt.close(fig)

    def test_metadata_style(self):
        fig = get_fig(get_sci())
        ls_meta = [t for t in fig.texts if "Rows" in t.get_text()]
        self.assertEqual(len(ls_meta), 1)
        self.assertEqual(ls_meta[0].get_color(), viewer.COLOR_ANNOTATION)
        self.assertAlmostEqual(ls_meta[0].get_fontsize(), plt.rcParams["font.size"] - 1)
        plt.close(fig)

    def test_dynamic_alpha_by_default(self):
        rst = get_sci()
        fig = get_fig(rst)
        self.assertEqual(
            fig.get_axes()[1].collections[0].get_alpha(),
            Univar.get_dynamic_alpha(n_points=79),
        )
        plt.close(fig)

    def test_cbar_tips(self):
        # data from 1 to 79
        for v_range, s_extend in [
            ([0, 100], "neither"),
            ([10, 100], "min"),
            ([10, 60], "both"),
        ]:
            with self.subTest(v_range=v_range):
                rst = get_sci()
                rst.view_specs["range"] = v_range
                fig = get_fig(rst)
                ax_data, ax_cbar = fig.get_axes()[1], fig.get_axes()[4]
                self.assertEqual(ax_cbar._colorbar.extend, s_extend)
                self.assertAlmostEqual(
                    ax_cbar.get_window_extent().y1,
                    ax_data.get_window_extent().y1,
                    places=3,
                )
                plt.close(fig)

    def test_scatter_band(self):
        fig = get_fig(get_sci())
        ax_data = fig.get_axes()[1]
        vct_x = ax_data.collections[0].get_offsets()[:, 0]
        n_lim = ax_data.get_xlim()[1] - ax_data.get_xlim()[0]
        self.assertAlmostEqual((vct_x.max() - vct_x.min()) / n_lim, 1 / 3, delta=0.01)
        plt.close(fig)

    def test_default_range_stays(self):
        rst = Elevation()
        self.assertEqual(rst.view_specs["range"], (0, 2000))
        rst.set_raster_metadata(metadata=METADATA)
        rst.set_data(grid=np.arange(80.0).reshape(8, 10))
        rst.update()
        self.assertEqual(rst.view_specs["range"], (0, 2000))

    def test_helper_geometry(self):
        rst = get_sci()
        # the helper goes beyond the grid
        helper = gpd.GeoDataFrame(geometry=[box(900, 1900, 1400, 2300)])
        rst.view_specs["helper_geometry"] = helper
        fig = get_fig(rst)
        ax_map = fig.get_axes()[0]
        self.assertEqual(len(ax_map.collections), 1)
        self.assertLessEqual(ax_map.get_xlim()[0], 900)
        self.assertGreaterEqual(ax_map.get_xlim()[1], 1400)
        self.assertLessEqual(ax_map.get_ylim()[0], 1900)
        self.assertGreaterEqual(ax_map.get_ylim()[1], 2300)
        plt.close(fig)

    def test_zoom_window(self):
        rst = get_sci()
        rst.view_specs["zoom_window"] = {"i_min": 2, "i_max": 4, "j_min": 1, "j_max": 6}
        fig = get_fig(rst)
        im = fig.get_axes()[0].images[0]
        self.assertEqual(im.get_array().shape, (2, 5))
        self.assertEqual(list(im.get_extent()), [1030, 1180, 2120, 2180])
        plt.close(fig)

    def test_grid_without_metadata(self):
        rst = SciRaster()
        rst.set_data(grid=np.arange(80.0).reshape(8, 10))
        fig = get_fig(rst)
        self.assertEqual(len(fig.get_axes()[0].images), 1)
        plt.close(fig)

    def test_large_grid_is_thinned(self):
        rst = SciRaster()
        rst.set_data(grid=np.arange(40000.0).reshape(200, 200))
        rst.N_DRAW = 100
        fig = get_fig(rst)
        ax_data, ax_hist, ax_cdf = fig.get_axes()[1:4]
        self.assertLessEqual(len(ax_data.collections[0].get_offsets()), 101)
        self.assertLessEqual(len(ax_cdf.lines[0].get_xdata()), 101)
        # the label of the mean comes from all data
        s_mean = ax_cdf.texts[0].get_text()
        self.assertIn(str(round(float(np.mean(rst.get_grid_data())), 2)), s_mean)
        self.assertEqual(s_mean, ax_hist.texts[0].get_text())
        plt.close(fig)

    def test_copy_structure(self):
        rst = get_sci()
        rst_new = SciRaster()
        rst_new.copy_structure(raster_ref=rst)
        self.assertEqual(rst_new.cellsize, 30)
        self.assertEqual(rst_new.get_extent(), [1000, 1300, 2000, 2240])

    def test_metadata_from_files(self):
        with tempfile.TemporaryDirectory() as folder:
            file_tif = os.path.join(folder, "sci.tif")
            with rasterio.open(
                file_tif,
                mode="w",
                driver="GTiff",
                width=10,
                height=8,
                count=1,
                dtype="float32",
                transform=rasterio.transform.from_origin(1000, 2240, 30, 30),
            ) as dst:
                dst.write(np.zeros((1, 8, 10), dtype="float32"))
            rst_new = SciRaster()
            rst_new.load_metadata(file_data=file_tif)
        self.assertEqual(rst_new.raster_metadata["ncols"], 10)
        self.assertEqual(rst_new.cellsize, 30)

    def test_aoi_from_interval(self):
        rst = get_sci()
        aoi = rst.get_aoi(by_value_lo=10, by_value_hi=19)
        self.assertIsInstance(aoi, AOI)
        self.assertEqual(int(np.sum(aoi.data)), 10)
        self.assertEqual(rst.get_stats()["count"], 79)


class TestQualiRaster(unittest.TestCase):

    def tearDown(self):
        plt.close("all")

    def test_stats_without_masked_cells(self):
        rst = get_quali()
        self.assertEqual(rst.get_grid_data().shape, (80,))
        self.assertEqual(rst.get_stats()["count"], 80)

    def test_stats_with_masked_cells(self):
        grid = np.ones(shape=(8, 10), dtype="uint8")
        grid[0, 0] = 255
        rst = get_quali(grid=grid)
        self.assertEqual(rst.get_stats()["count"], 79)

    def test_meaningless_getters(self):
        rst = get_quali()
        with self.assertRaises(ValueError):
            rst.get_normality()
        with self.assertRaises(ValueError):
            rst.get_cdf_gumbel()

    def test_view(self):
        rst = get_quali()
        for layout in ["full", "mini"]:
            with self.subTest(layout=layout):
                rst.view_specs["layout"] = layout
                fig = get_fig(rst)
                ax_map, ax_areas = fig.get_axes()
                self.assertEqual(len(ax_map.images), 1)
                self.assertEqual(
                    [t.get_text() for t in ax_areas.get_yticklabels()],
                    ["Forest", "Water"],
                )
                # each class has its color
                vct = ax_map.images[0].to_rgba(np.array([1, 2]))
                np.testing.assert_allclose(
                    vct[0][:3], mcolors.to_rgb("green"), atol=0.01
                )
                np.testing.assert_allclose(
                    vct[1][:3], mcolors.to_rgb("blue"), atol=0.01
                )
                plt.close(fig)

    def test_zonal_stats(self):
        rst = get_quali()
        sample = get_sci()
        df = rst.get_zonal_stats(raster_sample=sample)
        self.assertEqual(len(df), 2)
        self.assertEqual(df[f"{sample.varname}_count"].sum(), 79)
        # the sample is restored
        self.assertEqual(sample.get_stats()["count"], 79)

    def test_collection(self):
        col = RasterCollection(name="Collection")
        for i in range(2):
            rst = SciRaster(name=f"r{i}")
            rst.set_raster_metadata(metadata=METADATA)
            rst.set_data(grid=np.arange(80.0).reshape(8, 10) + i)
            rst.update()
            col.append(new_object=rst)
        self.assertTrue(col.is_same_grid())
        self.assertEqual(len(col.get_collection_stats()), 2)
        np.testing.assert_allclose(np.nanmean(col.to_mean().data), 40.0)

    def test_zones(self):
        zones = Zones()
        zones.set_raster_metadata(metadata=METADATA)
        zones.set_data(grid=np.arange(80, dtype="uint32").reshape(8, 10) % 4 + 1)
        self.assertEqual(len(zones.table), 4)
        self.assertEqual(zones.get_stats()["count"], 80)


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":
    # Script section
    # ===================================================================
    unittest.main()
    # ... {develop}
