# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Classes for statistical analysis of environmental and hydrological data.
"""

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import os
import pprint

# External imports
# =======================================================================
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors

# Project-level imports
# =======================================================================
from plans import viewer
from plans.root import DataSet
from plans.stochastic import bayes as _bayes
from plans.stochastic import binning as _binning
from plans.stochastic import curves as _curves
from plans.stochastic import descriptive as _descriptive
from plans.stochastic import frequency as _frequency
from plans.stochastic import metrics as _metrics
from plans.stochastic import normality as _normality
from plans.stochastic import sampling as _sampling
from plans.stochastic.curves import linear, power, power_zero


# CLASSES
# ***********************************************************************


class Univar(DataSet):
    """
    The Univariate object

    """

    def __init__(self, name="MyUnivar", alias="Uv0"):
        # ------------ set defaults ----------- #
        self.varfield = "v"
        self.varalias = "Var"
        self.varname = "Variable"
        self.units = "units"

        # ------------ call super ----------- #
        super().__init__(name=name, alias=alias)

        # overwriters

        # attributes
        self.var_min = None
        self.var_max = None
        self.start = None
        self.end = None

        self.stats_df = None
        self.freq_df = None
        self.weibull_df = None

        self.layouts = {
            "full": {
                "ncols": 24,
                "nrows": 16,
                "width": viewer.FIG_SIZES["M"]["w"],
                "height": viewer.FIG_SIZES["M"]["h"],
            },
            "mini": {
                "ncols": 24,
                "nrows": 12,
                "width": viewer.FIG_SIZES["M2"]["w"],
                "height": viewer.FIG_SIZES["M2"]["h"],
            },
            "simple": {
                "ncols": 24,
                "nrows": 12,
                "width": viewer.FIG_SIZES["S"]["w"],
                "height": viewer.FIG_SIZES["S"]["h"],
                "ax_hist": False,
                "ax_cdf": False,
            },
            "simple-shallow": {
                "ncols": 24,
                "nrows": 12,
                "width": viewer.FIG_SIZES["S2"]["w"],
                "height": viewer.FIG_SIZES["S2"]["h"],
                "ax_hist": False,
                "ax_cdf": False,
            },
            "qq": {
                "ncols": 24,
                "nrows": 12,
                "width": viewer.FIG_SIZES["S"]["w"],
                "height": viewer.FIG_SIZES["S"]["h"],
            },
            "default": {
                "ncols": 24,
                "nrows": 16,
                "width": viewer.FIG_SIZES["M"]["w"],
                "height": viewer.FIG_SIZES["M"]["h"],
            },
        }

    def _set_fields(self):
        """
        Set catalog fields names. Expected to increment superior methods.
        """
        # call super
        # ----------------------------------------------------------------
        super()._set_fields()

        # Univar fields
        self.units_field = "units"

    def get_metadata(self):
        """
        Get a dictionary with object metadata.
        Expected to increment superior methods.

        .. note::

            Metadata does **not** necessarily inclue all object attributes.

        :return: dictionary with all metadata
        :rtype: dict
        """
        # call super
        dc_meta = super().get_metadata()

        # customize local metadata
        dc_meta_local = {self.units_field: self.units}
        # update
        dc_meta.update(dc_meta_local)
        # move file_data to the end
        dc_meta.pop(self.field_file_data)
        dc_meta[self.field_file_data] = self.file_data
        return dc_meta

    def load_data(self, file_data, input_varfield=None, in_sep=";"):
        """
        Load data from file. Expected to overwrite superior methods.

        :param file_data: file path to data.
        :type file_data: str
        :return: None
        :rtype: None
        """

        # -------------- overwrite relative path inputs -------------- #
        self.file_data = os.path.abspath(file_data)

        # -------------- implement loading logic -------------- #

        s_key = self.varfield
        if input_varfield is not None:
            s_key = input_varfield

        default_columns = {
            s_key: float,
        }

        # -------------- call loading function -------------- #
        df = pd.read_csv(
            self.file_data,
            sep=in_sep,
            dtype=default_columns,
            usecols=list(default_columns.keys()),
        )

        # -------------- post-loading logic -------------- #
        df = df.rename(columns={s_key: self.varfield})
        df.dropna(inplace=True)
        self.data = df.copy()

        # -------------- update other mutables -------------- #
        self.update()

        # ... continues in downstream objects ... #

        return None

    def set_array(self, array):
        """
        Set array to data

        :param array: Numpy array
        :type array: :class:`numpy.ndarray`
        :return: None
        :rtype: None
        """
        self.data = pd.DataFrame({self.varfield: array})
        self.update()
        return None

    def update(self):
        """
        Refresh the attributes and statistics from the current data.

        :return: None
        :rtype: None
        """
        # ------------ call super ----------- #
        super().update()

        # update stats
        if self.data is not None:

            self.var_min = self.data[self.varfield].min()
            self.var_max = self.data[self.varfield].max()
            self.size = len(self.data)
            self.start = self.data.index.min()
            self.end = self.data.index.max()

            self.stats_df = self.get_basic_stats()
            self.freq_df = self.get_frequency()
            self.weibull_df = self.get_cdf_weibull()

            # view specs -- 5% margin keeps extremes off the panel edges
            margin = 0.05 * (self.var_max - self.var_min)
            self.view_specs["range"] = [self.var_min - margin, self.var_max + margin]

        # ... continues in downstream objects ... #
        return None

    # GET METHODS
    # ===================================================================

    def get_normality(self, clevel=0.95):
        """
        Get normality analysis using standard tests

        :param clevel: confidence level
        :type clevel: float
        :return: dataframe of assessment results
        :rtype: :class:`pandas.DataFrame`
        """
        data = self.data.dropna()[self.varfield].values
        return _normality.get_normality(data=data, clevel=clevel)

    def get_frequency(self):
        """
        Get data frequencies

        :return: result dataframe
        :rtype: :class:`pandas.DataFrame`
        """
        data = self.data.dropna()[self.varfield].values
        return _frequency.get_frequency(data=data)

    def get_basic_stats(self):
        """
        Get basic statistics data of the variable field.

        :return: DataFrame with statistics and their values.
        :rtype: :class:`pandas.DataFrame`
        """
        data = self.data.dropna()[self.varfield].values
        return _descriptive.get_basic_stats(data=data)

    def get_cdf_weibull(self):
        """
        Get the Weibull model for the data

        :return: model dataframe
        :rtype: :class:`pandas.DataFrame`
        """
        data = self.data.dropna()[self.varfield].values
        return _frequency.get_cdf_weibull(data=data)

    def get_cdf_gumbel(self):
        """
        Get the Gumbel CDF for the data (it assumes that is a maxima dataset)

        :return: multiple results from the assessment
        :rtype: dict
        """
        return _frequency.get_cdf_gumbel(df=self.data.dropna(), varfield=self.varfield)

    # PLOT METHODS
    # ===================================================================
    # Plotting methods
    def _plot(self, fig, gs, specs):
        """
        Plot on figure based on layout.

        :param fig: figure object
        :type fig: :class:`matplotlib.figure.Figure`
        :param gs: grid of the figure
        :type gs: :class:`matplotlib.gridspec.GridSpec`
        :param specs: plot specification dictionary
        :type specs: dict
        :return: figure object
        :rtype: :class:`matplotlib.figure.Figure`
        """
        formatter = mticker.ScalarFormatter(useOffset=False, useMathText=False)
        formatter.set_scientific(False)  # Ensure scientific notation is off

        # RANGE
        # -------------------------------------------------------------------
        if self.stats_df is None:
            self.stats_df = self.get_basic_stats()
        # handle if none
        if specs["range"] is None:
            p_low = self.stats_df.loc[
                self.stats_df["statistic"] == "p01", "value"
            ].values[0]
            p_hi = self.stats_df.loc[
                self.stats_df["statistic"] == "p99", "value"
            ].values[0]
            rng = p_hi - p_low
            rng_margin = rng * 0.1
            specs["range"] = (p_low - rng_margin, p_hi + rng_margin)

        # TITLE
        # -------------------------------------------------------------------
        if specs["title"] is not None:
            plt.suptitle(specs["title"], fontsize=9)

        # AXES
        # -------------------------------------------------------------------
        fig = self._build_axes(fig=fig, gs=gs, specs=specs)

        # PLOT
        # -------------------------------------------------------------------
        if specs["layout"] == "qq":
            self._plot_qq(fig=fig, specs=specs, formatter=formatter)
        else:
            self._plot_full(fig=fig, specs=specs, formatter=formatter)

        return fig

    def _plot_full(self, fig, specs, formatter):
        """
        Plot the data, histogram and CDF panels, and the statistics table.

        :param fig: figure object with the axes already built
        :type fig: :class:`matplotlib.figure.Figure`
        :param specs: plot specification dictionary
        :type specs: dict
        :param formatter: formatter of the y axis
        :type formatter: :class:`matplotlib.ticker.Formatter`
        :return: None
        :rtype: None
        """
        if self.weibull_df is None:
            self.weibull_df = self.get_cdf_weibull()

        all_axes = fig.get_axes()

        # DATA
        ax_data = False
        if specs["ax_data"] is not False:
            ax_data = all_axes[specs["ax_data"]]

        # HIST
        ax_hist = False
        if specs["ax_hist"] is not False:
            ax_hist = all_axes[specs["ax_hist"]]

        # CDF
        ax_cdf = False
        if specs["ax_cdf"] is not False:
            ax_cdf = all_axes[specs["ax_cdf"]]

        # CLEANUP
        # -------------------------------------------------------------------
        df_clean = self.data.dropna()
        data = df_clean[self.varfield].values

        # PLOT DATA
        # -------------------------------------------------------------------
        if specs["data_plot"] == "boxplot":
            Univar.plot_boxplot(
                data=data,
                ax=ax_data,
                specs=specs,
                formatter=formatter,
            )
        else:
            Univar.plot_scatter(
                data=data,
                ax=ax_data,
                specs=specs,
                formatter=formatter,
            )

        # PLOT HIST
        # -------------------------------------------------------------------
        Univar.plot_histh(
            data=data,
            ax=ax_hist,
            specs=specs,
            formatter=formatter,
        )

        # PLOT CDF
        # -------------------------------------------------------------------
        Univar.plot_cdf(
            cdf_df=self.weibull_df,
            ax=ax_cdf,
            specs=specs,
            formatter=formatter,
        )

        # PLOT STATS
        # -------------------------------------------------------------------
        if specs["layout"] == "full":
            Univar.plot_stats(
                fig=fig,
                stats_df=self.stats_df,
                x=specs["x_stats"],
                y=specs["y_stats"],
                sep=specs["x_stats_sep"],
            )

        return None

    def _plot_qq(self, fig, specs, formatter):
        """
        Plot the Q-Q panel.

        :param fig: figure object with the axes already built
        :type fig: :class:`matplotlib.figure.Figure`
        :param specs: plot specification dictionary
        :type specs: dict
        :param formatter: formatter of the y axis
        :type formatter: :class:`matplotlib.ticker.Formatter`
        :return: None
        :rtype: None
        """
        Univar.plot_qq(
            data=self.data[self.varfield].dropna().values,
            ax=fig.get_axes()[0],
            specs=specs,
            formatter=formatter,
        )
        return None

    def _build_axes(self, fig, gs, specs):
        """
        Add subplots to figure based on layout.

        :param fig: figure object
        :type fig: :class:`matplotlib.figure.Figure`
        :param gs: grid of the figure
        :type gs: :class:`matplotlib.gridspec.GridSpec`
        :param specs: plot specification dictionary
        :type specs: dict
        :return: figure object
        :rtype: :class:`matplotlib.figure.Figure`
        """
        if specs["layout"] == "simple":
            fig.add_subplot(gs[2:12, 4:])

        elif specs["layout"] == "simple-shallow":
            # lower top, so the panel title sits below the figure title
            fig.add_subplot(gs[4:10, 4:])

        elif specs["layout"] == "qq":
            fig.add_subplot(gs[2:10, 4:])

        else:
            fig.add_subplot(gs[2:10, 2:10])
            fig.add_subplot(gs[2:10, 12:17])
            fig.add_subplot(gs[2:10, 19:])

        return fig

    def _get_fig_specs(self):
        """
        Get figure specs by merging view specs, layout specs and grid specs.

        :return: figure specs
        :rtype: dict
        """
        specs = self.view_specs.copy()

        # handle layout
        layout = specs["layout"]
        if layout not in self.layouts:
            raise ValueError(
                f"Unknown layout '{layout}'. Options: {list(self.layouts.keys())}"
            )

        # update sizes and panels
        specs.update(self.layouts[layout].copy())

        # update gridspecs
        specs.update(viewer.GRID_SPECS)

        return specs

    def _set_view_specs(self):
        """
        Set view specifications. Expected to overwrite superior methods.

        :return: None
        :rtype: None
        """
        super()._set_view_specs()
        self.view_specs.update(
            {
                # layout
                "style": "wien",
                "layout": "full",
                # data plot: "scatter" or "boxplot"
                "data_plot": "scatter",
                # titles
                "subtitle_data": "Data Points",
                "subtitle_box": "Boxplot",
                "subtitle_hist": "Histogram",
                "subtitle_cdf": "CDF",
                "subtitle_qq": "Q-Q",
                # fields
                "yvar_field": self.varfield,
                "xvar": "i",
                "yvar": self.varname,
                # axis labels
                "xlabel": self.varname,
                "xlabel_cdf": "P(X)",
                "xlabel_qq": "Normal quantiles",
                "ylabel": self.units,
                # data labels
                "data_label": self.name,
                "data_legend": False,
                # colors
                "color": "tab:grey",
                "color_hist": "tab:grey",
                "color_cdf": "black",
                "color_mean": "red",
                "color_mean_text": None,
                # cmaps
                "scheme_cmap": "equal",
                "n_classes_cmap": 5,
                "cmap": "viridis",
                # alphas
                "alpha": 0.8,
                "alpha_hist": 1,
                "alpha_cdf": 1,
                # ranges
                "range": None,
                "range_x": None,
                # mean
                "plot_mean": True,
                "plot_mean_data": False,
                "linestyle_mean": "solid",
                "pad_mean": 1,
                "plot_mean_label": True,
                # histogram
                "hist_density": True,  # todo check this may be deprecated
                "bins": 20,
                "bins_density": False,
                # axes
                "ax_data": 0,
                "ax_hist": 1,
                "ax_cdf": 2,
                # stats locators
                "x_stats": 0.01,
                "x_stats_sep": 0.2,
                "y_stats": 0.3,
                # zorder
                "zorder_data": 1,
                "zorder_histh": 1,
                "zorder_cdf": 1,
                # scatter
                "scatter_factor": 4,
                "colorize_scatter": False,
                # boxplot
                "box_width": 0.4,
                "box_showfliers": True,
            }
        )

        del self.view_specs["width"]
        del self.view_specs["height"]

        return None

    def view(self, show=True, return_fig=False):
        """
        Get the visualization. Layout is set by ``view_specs["layout"]``. The
        options are the keys of the ``layouts`` attribute.

        **Layouts**, set by ``view_specs["layout"]``:

        ==================  ===================================================
        Layout              Panels
        ==================  ===================================================
        ``full``            Data, histogram and CDF, with the statistics table.
        ``mini``            Data, histogram and CDF.
        ``simple``          Data only.
        ``simple-shallow``  Data only, in a shallow figure.
        ``qq``              Q-Q plot.
        ``default``         Same panels of ``mini``, in the figure of ``full``.
        ==================  ===================================================

        **View specs**, set by ``view_specs[key] = value`` before the call:

        ====================  =================  =====================================================================================================================
        Key                   Default            Description
        ====================  =================  =====================================================================================================================
        ``style``             ``"wien"``         Name of the plot style. See :func:`plans.viewer.set_style`.
        ``folder``            auto               Folder of the saved figure.
        ``filename``          auto               Name of the saved figure, without extension.
        ``fig_format``        ``"jpg"``          Format of the saved figure.
        ``dpi``               ``300``            Resolution of the saved figure.
        ``title``             auto               Title of the figure.
        ``xvar``              auto               Not in use.
        ``yvar``              auto               Not in use.
        ``xlabel``            auto               Label of the x axis.
        ``ylabel``            auto               Label of the y axis.
        ``color``             ``"tab:grey"``     Color of the data.
        ``xmin``              None               Not in use.
        ``xmax``              None               Not in use.
        ``ymin``              None               Not in use.
        ``ymax``              None               Not in use.
        ``layout``            ``"full"``         Name of the layout. See the table of layouts.
        ``data_plot``         ``"scatter"``      Plot of the data panel: ``"scatter"`` or ``"boxplot"``.
        ``subtitle_data``     ``"Data Points"``  Title of the data panel. None hides it.
        ``subtitle_box``      ``"Boxplot"``      Title of the data panel, if a boxplot.
        ``subtitle_hist``     ``"Histogram"``    Title of the histogram. None hides it.
        ``subtitle_cdf``      ``"CDF"``          Title of the CDF. None hides it.
        ``subtitle_qq``       ``"Q-Q"``          Title of the Q-Q panel. None hides it.
        ``yvar_field``        auto               Column of values. Set with the data.
        ``xlabel_cdf``        ``"P(X)"``         Label of the x axis of the CDF.
        ``xlabel_qq``         auto               Label of the x axis of the Q-Q panel.
        ``data_label``        auto               Label of the data in the legend.
        ``data_legend``       ``False``          Show the legend of the data panel.
        ``color_hist``        ``"tab:grey"``     Color of the histogram.
        ``color_cdf``         ``"black"``        Color of the CDF.
        ``color_mean``        ``"red"``          Color of the mean line.
        ``color_mean_text``   None               Color of the mean label. None is black.
        ``scheme_cmap``       ``"equal"``        Classes of the color map: ``"equal"``, ``"quantiles"`` or other schemes of :func:`plans.stochastic.binning.get_bins`.
        ``n_classes_cmap``    ``5``              Number of classes of the color map.
        ``cmap``              ``"viridis"``      Name of the color map.
        ``alpha``             ``0.8``            Opacity of the data.
        ``alpha_hist``        ``1``              Opacity of the histogram.
        ``alpha_cdf``         ``1``              Opacity of the CDF.
        ``range``             None               Range of the y axis, as ``[low, high]``. None is set from the data.
        ``range_x``           None               Range of the x axis, as ``[low, high]``. None is set from the data.
        ``plot_mean``         ``True``           Show the mean line.
        ``plot_mean_data``    ``False``          Show the mean line also on the data panel.
        ``linestyle_mean``    ``"solid"``        Line style of the mean.
        ``pad_mean``          ``1``              Spaces between the mean label and its line.
        ``plot_mean_label``   ``True``           Show the mean label.
        ``hist_density``      ``True``           Not in use.
        ``bins``              ``20``             Number of histogram bins, or the width of the bins if ``bins_density``.
        ``bins_density``      ``False``          Take ``bins`` as the width of the bins.
        ``ax_data``           ``0``              Internal. Index of the data axis.
        ``ax_hist``           ``1``              Internal. Index of the histogram axis. False has no histogram.
        ``ax_cdf``            ``2``              Internal. Index of the CDF axis. False has no CDF.
        ``x_stats``           ``0.01``           Horizontal position of the statistics table, as a share of the figure.
        ``x_stats_sep``       ``0.2``            Space between columns of the statistics table.
        ``y_stats``           ``0.3``            Vertical position of the statistics table, as a share of the figure.
        ``zorder_data``       ``1``              Drawing order of the data.
        ``zorder_histh``      ``1``              Drawing order of the histogram.
        ``zorder_cdf``        ``1``              Drawing order of the CDF.
        ``scatter_factor``    ``4``              Size of the scatter markers.
        ``colorize_scatter``  ``False``          Color the scatter markers by the color map.
        ``box_width``         ``0.4``            Width of the boxplot.
        ``box_showfliers``    ``True``           Show the outliers of the boxplot.
        ``gs_*``              auto               Internal. Replaced by the shared grid of :mod:`plans.viewer`.
        ====================  =================  =====================================================================================================================

        :param show: option for showing instead of saving
        :type show: bool
        :param return_fig: option for returning the figure object
        :type return_fig: bool
        :return: figure object if ``return_fig`` is True, else None
        :rtype: :class:`matplotlib.figure.Figure` or None
        """
        if self.data is None:
            raise ValueError("No data to view. Set the data first")

        # SPECS
        # -------------------------------------------------------------------
        specs = self._get_fig_specs()

        # BUILD
        # -------------------------------------------------------------------
        # build from specs
        fig, gs = viewer.build_fig(specs=specs)

        # PLOT
        # -------------------------------------------------------------------
        fig = self._plot(fig=fig, gs=gs, specs=specs)

        # SHIP
        # -------------------------------------------------------------------
        # create path
        file_path = "{}/{}.{}".format(
            specs["folder"], specs["filename"], specs["fig_format"]
        )
        if return_fig:
            return fig
        else:
            viewer.ship_fig(fig=fig, show=show, file_output=file_path, dpi=specs["dpi"])

    # STATIC METHODS
    # ===================================================================

    @staticmethod
    def plot_mean(ax, y_mu, xmin, xmax, specs):
        """
        Plot the mean as a horizontal line, with an optional label.

        :param ax: axis to plot on. Nothing is plotted if False
        :type ax: :class:`matplotlib.axes.Axes` or bool
        :param y_mu: mean value
        :type y_mu: float
        :param xmin: start of the line
        :type xmin: float
        :param xmax: end of the line
        :type xmax: float
        :param specs: plot specification dictionary (from ``view_specs``)
        :type specs: dict
        :return: None
        :rtype: None
        """
        if not ax:
            return None

        ax.hlines(
            y=y_mu,
            xmin=xmin,
            xmax=xmax,
            colors=specs["color_mean"],
            linestyle=specs["linestyle_mean"],
        )

        if specs["color_mean_text"] is None:
            specs["color_mean_text"] = "black"

        if specs["plot_mean_label"]:
            pad = specs["pad_mean"] * " "
            s = r"{}$\mu$ = {}".format(pad, round(y_mu, 2))
            ax.annotate(
                s,
                xy=(xmin, y_mu),
                xytext=(1, 3),
                textcoords="offset points",
                color=specs["color_mean_text"],
            )
        return None

    @staticmethod
    def plot_scatter(data, ax, specs, formatter=None):
        """
        Plot the data points in their original order.

        :param data: vector of data without nan values
        :type data: :class:`numpy.ndarray`
        :param ax: axis to plot on. Nothing is plotted if False
        :type ax: :class:`matplotlib.axes.Axes` or bool
        :param specs: plot specification dictionary (from ``view_specs``)
        :type specs: dict
        :param formatter: [optional] formatter of the y axis
        :type formatter: :class:`matplotlib.ticker.Formatter`
        :return: None
        :rtype: None
        """
        if not ax:
            return None
        x_values = np.arange(len(data))
        x_factor = specs["scatter_factor"]
        # handle scheme
        if specs["colorize_scatter"]:
            color_data = _binning.classify(
                data=data,
                n_classes=specs["n_classes_cmap"],
                scheme=specs["scheme_cmap"],
            )
            color_cmap = viewer.get_discrete_cmap(
                n_classes=specs["n_classes_cmap"], base_cmap_name=specs["cmap"]
            )
            # plot
            ax.scatter(
                x_values,
                data,
                marker=".",
                c=color_data,
                cmap=color_cmap,
                alpha=specs["alpha"],
                s=0.8 * viewer.MM_TO_PT,
                zorder=specs["zorder_data"],
            )
        else:
            ax.scatter(
                x_values,
                data,
                marker=".",
                color=specs["color"],
                alpha=specs["alpha"],
                s=0.8 * viewer.MM_TO_PT,
                zorder=specs["zorder_data"],
            )

        if specs["subtitle_data"] is not None:
            ax.set_title(specs["subtitle_data"], loc="left")

        ax.set_ylim(specs["range"])
        ax.set_xlabel(specs["xlabel"])
        ax.set_ylabel(specs["ylabel"])
        ax.grid(axis="x", visible=False)

        if formatter is not None:
            ax.yaxis.set_major_formatter(formatter)

        # handle x axis
        n_size = len(data)
        x_low = -x_factor * n_size
        x_hi = n_size + (x_factor * n_size)
        ax.set_xlim(x_low, x_hi)
        ax.set_xticks([])

        # handle cbars
        # ------------ cbar plot ------------
        if specs["colorize_scatter"]:
            Univar.plot_cbar(
                data=data,
                ax=ax,
                scheme=specs["scheme_cmap"],
                cmap=specs["cmap"],
                n_classes=specs["n_classes_cmap"],
                side="right",
            )

        # PLOT MEAN LINE
        # -------------------------------------------------------------------
        if specs["plot_mean_data"]:
            # data
            Univar.plot_mean(
                ax,
                y_mu=np.nanmean(data),
                xmin=x_low,
                xmax=x_hi,
                specs=specs,
            )

        return (x_low, x_hi)

    @staticmethod
    def plot_boxplot(data, ax, specs, formatter=None):
        """
        Plot a vertical boxplot of the data, sharing the y range of the other panels.

        :param data: vector of data without nan values
        :type data: :class:`numpy.ndarray`
        :param ax: target axes. If False, nothing is plotted.
        :type ax: :class:`matplotlib.axes.Axes`
        :param specs: plot specification dictionary (from ``view_specs``)
        :type specs: dict
        :param formatter: [optional] y axis tick formatter
        :type formatter: :class:`matplotlib.ticker.Formatter`
        :return: None
        :rtype: None
        """
        if not ax:
            return None

        # box at x = 0, whiskers at 1.5 IQR
        ax.boxplot(
            data,
            positions=[0],
            widths=specs["box_width"],
            showfliers=specs["box_showfliers"],
            patch_artist=True,
            boxprops={"facecolor": specs["color"], "alpha": specs["alpha"]},
            medianprops={"color": "black"},
            flierprops={
                "marker": ".",
                "markersize": 3,
                "markerfacecolor": specs["color"],
                "markeredgecolor": "none",
            },
            zorder=specs["zorder_data"],
        )

        if specs["subtitle_box"] is not None:
            ax.set_title(specs["subtitle_box"], loc="left")

        ax.set_ylim(specs["range"])
        ax.set_xlim(-1, 1)
        ax.set_xticks([])
        ax.set_xlabel(specs["xlabel"])
        ax.set_ylabel(specs["ylabel"])
        ax.grid(axis="x", visible=False)

        if formatter is not None:
            ax.yaxis.set_major_formatter(formatter)

        # mean line
        if specs["plot_mean_data"]:
            Univar.plot_mean(ax=ax, y_mu=np.nanmean(data), xmin=-1, xmax=1, specs=specs)

        return None

    @staticmethod
    def plot_histh(data, ax, specs, formatter=None):
        """
        Plot a horizontal histogram.

        :param data: vector of data without nan values
        :type data: :class:`numpy.ndarray`
        :param ax: axis to plot on. Nothing is plotted if False
        :type ax: :class:`matplotlib.axes.Axes` or bool
        :param specs: plot specification dictionary (from ``view_specs``)
        :type specs: dict
        :param formatter: [optional] formatter of the y axis
        :type formatter: :class:`matplotlib.ticker.Formatter`
        :return: output of the histogram, or None if there is no axis
        :rtype: tuple or None
        """

        # todo dry --- evaluate to remove the range_data parameter
        # ------- local functions --------
        def _get_max(std_values, data):
            data_max = np.max(data)
            closest_max_index = np.argmin(np.abs(np.array(std_values) - data_max))
            _id = closest_max_index + 1
            if _id >= len(std_values):
                _id = len(std_values) - 1
            return std_values[_id]

        h = None

        if not ax:
            return None

        # Standard x-axis maximum values for hist
        sdmax1 = list(np.linspace(1, 9, 9) / 100)
        sdmax2 = list(np.linspace(10, 100, 10) / 100)
        standard_max_values = sdmax1 + sdmax2

        # handle data range
        data_range = specs["range"]
        if data_range is None:
            data_range = [np.nanmin(data), np.nanmax(data)]

        # handle bins
        n_bins = specs["bins"]
        if specs["bins_density"]:
            n_units = n_bins
            d_range = [np.nanmin(data), np.nanmax(data)]
            n_bins = _binning.get_nbins_density(n_units=n_units, data_range=d_range)

        # plot horizontal hist
        h = ax.hist(
            data,
            bins=n_bins,
            color=specs["color_hist"],
            alpha=specs["alpha_hist"],
            histtype=specs.get("histtype", "bar"),
            orientation="horizontal",
            weights=np.ones(len(data)) / len(data),
            zorder=specs["zorder_histh"],
        )
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(1))
        if specs["subtitle_hist"] is not None:
            ax.set_title(specs["subtitle_hist"], loc="left")

        # Get the maximum value from the data
        xmax = _get_max(standard_max_values, h[0]) * 1.1
        ax.set_xlim(0, xmax)
        ax.set_ylim(data_range)
        ax.set_xlabel("%")
        if formatter is not None:
            ax.yaxis.set_major_formatter(formatter)

        # PLOT MEAN
        # --------------------------------------------------
        if specs["plot_mean"]:
            # hist
            Univar.plot_mean(
                ax,
                y_mu=np.nanmean(data),
                xmin=0,
                xmax=1,
                specs=specs,
            )

        return h

    @staticmethod
    def plot_cdf(cdf_df, ax, specs, formatter=None, px_field="P(X)", var_field="Data"):
        """
        Plot the CDF, as exceedance probability.

        :param cdf_df: dataframe of the CDF
        :type cdf_df: :class:`pandas.DataFrame`
        :param ax: axis to plot on. Nothing is plotted if False
        :type ax: :class:`matplotlib.axes.Axes` or bool
        :param specs: plot specification dictionary (from ``view_specs``)
        :type specs: dict
        :param formatter: [optional] formatter of the y axis
        :type formatter: :class:`matplotlib.ticker.Formatter`
        :param px_field: name of the probability field
        :type px_field: str
        :param var_field: name of the variable field
        :type var_field: str
        :return: None
        :rtype: None
        """

        if not ax:
            return None

        # PLOT CDF
        # --------------------------------------------------
        ax.plot(
            cdf_df[px_field],
            cdf_df[var_field],
            color=specs["color_cdf"],
            alpha=specs["alpha_cdf"],
            zorder=specs["zorder_cdf"],
        )

        if specs["subtitle_cdf"] is not None:
            ax.set_title(specs["subtitle_cdf"], loc="left")

        ax.set_xlabel(specs["xlabel_cdf"])
        ax.set_xlim(-0.05, 1.05)
        ax.set_ylim(specs["range"])

        if formatter is not None:
            ax.yaxis.set_major_formatter(formatter)
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(1))

        # PLOT MEAN
        # --------------------------------------------------
        if specs["plot_mean"]:
            Univar.plot_mean(
                ax,
                y_mu=cdf_df[var_field].mean(),
                xmin=-0.05,
                xmax=1.05,
                specs=specs,
            )

        return None

    @staticmethod
    def plot_qq(data, ax, specs, formatter=None):
        """
        Plot data quantiles against normal quantiles. The line is the normal
        distribution with the mean and standard deviation of the data.

        :param data: vector of data without nan values
        :type data: :class:`numpy.ndarray`
        :param ax: axis to plot on. Nothing is plotted if False
        :type ax: :class:`matplotlib.axes.Axes` or bool
        :param specs: plot specification dictionary (from ``view_specs``)
        :type specs: dict
        :param formatter: [optional] formatter of the y axis
        :type formatter: :class:`matplotlib.ticker.Formatter`
        :return: None
        :rtype: None
        """
        if not ax:
            return None

        df_qq = _descriptive.qqplot(data=data)
        vct_t = df_qq["T-Quantiles"].values
        ax.plot(
            vct_t,
            np.mean(data) + np.std(data) * vct_t,
            color=specs["color_mean"],
            linestyle=specs["linestyle_mean"],
            zorder=specs["zorder_data"],
        )
        ax.scatter(
            vct_t,
            df_qq["Data"],
            marker=".",
            color=specs["color"],
            alpha=specs["alpha"],
            s=0.8 * viewer.MM_TO_PT,
            zorder=specs["zorder_data"],
        )
        if specs["subtitle_qq"] is not None:
            ax.set_title(specs["subtitle_qq"], loc="left")
        ax.set_xlabel(specs["xlabel_qq"])
        ax.set_ylabel(specs["ylabel"])
        ax.set_xlim(specs["range_x"])
        ax.set_ylim(specs["range"])
        if formatter is not None:
            ax.yaxis.set_major_formatter(formatter)

        return None

    @staticmethod
    def plot_stats(fig, stats_df, x=0.5, y=0.4, sep=0.2):
        """
        Plot two columns of basic statistics as text on the figure.

        :param fig: figure object
        :type fig: :class:`matplotlib.figure.Figure`
        :param stats_df: dataframe of basic statistics
        :type stats_df: :class:`pandas.DataFrame`
        :param x: position of the first column, in figure fraction
        :type x: float
        :param y: position of the top of the columns, in figure fraction
        :type y: float
        :param sep: distance between the columns, in figure fraction
        :type sep: float
        :return: figure object
        :rtype: :class:`matplotlib.figure.Figure`
        """

        # Helper function to plot a single column of stats
        def _plot_column(x_position, stats_list, start_y):
            current_y = start_y
            for stat in stats_list:
                # Handle "Median" special case if it's coming from ls_stats that uses it
                display_stat = "p50" if stat == "median" else stat

                # Ensure the stat exists in the DataFrame before attempting to access
                stat_row = stats_df.loc[stats_df["statistic"] == display_stat]
                if not stat_row.empty:
                    s_value = stat_row["value"].values[0]
                    s_head = stat  # Use the original name for display if needed, or display_stat

                    # Determine formatting based on value magnitude
                    if abs(s_value) > 1_000_000:
                        s_line = "{:>10}: {:<10.2e}".format(s_head, s_value)
                    elif stat == "count":
                        s_line = "{:>10}: {:<10}".format(s_head, int(s_value))
                    else:
                        s_line = "{:>10}: {:<10.2f}".format(s_head, s_value)

                    current_y -= n_step
                    plt.text(
                        x=x_position,
                        y=current_y,
                        s=s_line,
                        fontdict={"family": "monospace"},
                        transform=fig.transFigure,
                    )
                else:
                    # Optional: Handle cases where a stat might not be found
                    # print(f"Warning: Statistic '{display_stat}' not found in DataFrame.")
                    pass

        n_step = 0.03

        # First column of statistics
        ls_stats_col1 = [
            "count",
            "sum",
            "mean",
            "median",  # This will be mapped to "P50" internally by the helper
            "sd",
            "min",
            "max",
        ]
        _plot_column(x, ls_stats_col1, y - 0.01)

        # Second column of statistics
        ls_stats_col2 = [
            "p05",
            "p10",
            "p25",
            "p50",
            "p75",
            "p90",
            "p95",
        ]
        _plot_column(x + sep, ls_stats_col2, y - 0.01)

        return fig

    @staticmethod
    def plot_cbar(
        data, ax, scheme, cmap="viridis", n_classes=5, side="right", width_factor=16
    ):
        """
        Plot a vertical color bar of the data classes, inside the axis.

        :param data: vector of data
        :type data: :class:`numpy.ndarray`
        :param ax: axis to plot on
        :type ax: :class:`matplotlib.axes.Axes`
        :param scheme: classification scheme, such as ``equal`` or ``quantiles``
        :type scheme: str
        :param cmap: name of the color map
        :type cmap: str
        :param n_classes: number of classes
        :type n_classes: int
        :param side: side of the axis, ``left`` or ``right``
        :type side: str
        :param width_factor: width of the bar as a fraction of the axis (1 over this value)
        :type width_factor: float
        :return: None
        :rtype: None
        """

        # handle bins
        bins = _binning.get_bins(data=data, n_bins=n_classes, scheme=scheme)

        # handle egde cases
        n_bins = len(bins)
        if n_bins <= n_classes:
            n_classes = n_bins - 1

        # handle colors
        custom_cmap = viewer.get_discrete_cmap(n_classes=n_classes, base_cmap_name=cmap)
        colors = []
        for i in range(n_classes):
            colors.append(custom_cmap.colors[i])

        # handle position
        xlims = ax.get_xlim()
        bar_w = abs(xlims[1] - xlims[0]) / width_factor
        if side == "left":
            vrange = [xlims[0], xlims[0] + bar_w]
        elif side == "right":
            vrange = [xlims[1] - bar_w, xlims[1]]
        else:
            vrange = [xlims[0], xlims[0] + bar_w]

        # plotting loop
        n_classes = len(colors)
        for i in range(n_classes):
            lower_bound = bins[i]
            upper_bound = bins[i + 1]
            color = colors[i]
            ax.fill_between(
                vrange, lower_bound, upper_bound, color=color, edgecolor="none"
            )

        return None

    @staticmethod
    def test_distribution(test_name, stat, p, clevel=0.95, distr="normal"):
        """See :func:`plans.stochastic.normality.test_distribution`."""
        return _normality.test_distribution(
            test_name=test_name, stat=stat, p=p, clevel=clevel, distr=distr
        )

    @staticmethod
    def test_normality_ks(data, clevel=0.95):
        """See :func:`plans.stochastic.normality.test_normality_ks`."""
        return _normality.test_normality_ks(data=data, clevel=clevel)

    @staticmethod
    def test_normality_sw(data, clevel=0.95):
        """See :func:`plans.stochastic.normality.test_normality_sw`."""
        return _normality.test_normality_sw(data=data, clevel=clevel)

    @staticmethod
    def test_normality_dp(data, clevel=0.95):
        """See :func:`plans.stochastic.normality.test_normality_dp`."""
        return _normality.test_normality_dp(data=data, clevel=clevel)

    @staticmethod
    def get_tx(fx):
        """Return period. See :func:`plans.stochastic.frequency.get_tx`."""
        return _frequency.get_tx(fx=fx)

    @staticmethod
    def gumbel_fx(x, a, b):
        """Gumbel F(X). See :func:`plans.stochastic.frequency.gumbel_fx`."""
        return _frequency.gumbel_fx(x=x, a=a, b=b)

    @staticmethod
    def gumbel_tx(x, a, b):
        """Gumbel T(X). See :func:`plans.stochastic.frequency.gumbel_tx`."""
        return _frequency.gumbel_tx(x=x, a=a, b=b)

    @staticmethod
    def gumbel_freqfactor(tx=2):
        """See :func:`plans.stochastic.frequency.gumbel_freqfactor`."""
        return _frequency.gumbel_freqfactor(tx=tx)

    @staticmethod
    def gumbel_se(std_sample, n_sample, tx):
        """Gumbel SE. See :func:`plans.stochastic.frequency.gumbel_se`."""
        return _frequency.gumbel_se(std_sample=std_sample, n_sample=n_sample, tx=tx)

    @staticmethod
    def empirical_px(ranks):
        """Empirical P(X). See :func:`plans.stochastic.frequency.empirical_px`."""
        return _frequency.empirical_px(ranks=ranks)

    @staticmethod
    def weibull_px(ranks):
        """Weibull P(X). See :func:`plans.stochastic.frequency.weibull_px`."""
        return _frequency.weibull_px(ranks=ranks)

    @staticmethod
    def gringorten_px(ranks):
        """See :func:`plans.stochastic.frequency.gringorten_px`."""
        return _frequency.gringorten_px(ranks=ranks)

    @staticmethod
    def sample_gamma(
        size, shape=3, scale=1, shape_mode=None, n_min=None, n_max=None, rng=None
    ):
        """Sample gamma. See :func:`plans.stochastic.sampling.sample_gamma`."""
        return _sampling.sample_gamma(
            size=size,
            shape=shape,
            scale=scale,
            shape_mode=shape_mode,
            n_min=n_min,
            n_max=n_max,
            rng=rng,
        )

    @staticmethod
    def get_nbins_fd(data):
        """Freedman-Diaconis bins. See :func:`plans.stochastic.binning.get_nbins_fd`."""
        return _binning.get_nbins_fd(data=data)

    @staticmethod
    def get_nbins_sturges(data):
        """Sturges bins. See :func:`plans.stochastic.binning.get_nbins_sturges`."""
        return _binning.get_nbins_sturges(data=data)

    @staticmethod
    def get_nbins_scott(data):
        """Scott bins. See :func:`plans.stochastic.binning.get_nbins_scott`."""
        return _binning.get_nbins_scott(data=data)

    @staticmethod
    def get_nbins_density(n_units, data_range):
        """Bins by width. See :func:`plans.stochastic.binning.get_nbins_density`."""
        return _binning.get_nbins_density(n_units=n_units, data_range=data_range)

    @staticmethod
    def get_nbins_by_rule(data, rule=None):
        """Bins by rule. See :func:`plans.stochastic.binning.get_nbins_by_rule`."""
        return _binning.get_nbins_by_rule(data=data, rule=rule)

    @staticmethod
    def get_histogram(data, bins=100, rule=None):
        """Histogram. See :func:`plans.stochastic.binning.get_histogram`."""
        return _binning.get_histogram(data=data, bins=bins, rule=rule)

    @staticmethod
    def qqplot(data):
        """QQ-plot data. See :func:`plans.stochastic.descriptive.qqplot`."""
        return _descriptive.qqplot(data=data)

    @staticmethod
    def trace_variance(data):
        """See :func:`plans.stochastic.descriptive.trace_variance`."""
        return _descriptive.trace_variance(data=data)

    @staticmethod
    def get_bins(data, n_bins=5, scheme="equal"):
        """Class boundaries. See :func:`plans.stochastic.binning.get_bins`."""
        return _binning.get_bins(data=data, n_bins=n_bins, scheme=scheme)

    @staticmethod
    def bins_equal(data, n_bins):
        """Equal bins. See :func:`plans.stochastic.binning.bins_equal`."""
        return _binning.bins_equal(data=data, n_bins=n_bins)

    @staticmethod
    def bins_quantiles(data, n_bins=5):
        """Quantile bins. See :func:`plans.stochastic.binning.bins_quantiles`."""
        return _binning.bins_quantiles(data=data, n_bins=n_bins)

    @staticmethod
    def classify(data, bins=None, n_classes=5, scheme="equal"):
        """Classify data. See :func:`plans.stochastic.binning.classify`."""
        return _binning.classify(
            data=data, bins=bins, n_classes=n_classes, scheme=scheme
        )

    @staticmethod
    def quantiles_classify(data, n_classes=5):
        """See :func:`plans.stochastic.binning.quantiles_classify`."""
        return _binning.quantiles_classify(data=data, n_classes=n_classes)


class GeoUnivar(Univar):
    """
    Univariate data with locations, held in a ``GeoDataFrame``. Adds a map panel
    to the visuals of :class:`Univar`.
    """

    def __init__(self, name="MyGeoUnivar", alias="GV0"):
        # call super
        super().__init__(name=name, alias=alias)
        self.layer_name = None

        # the map panel needs its own layouts
        self.layouts = {
            "full": {
                "ncols": 34,
                "nrows": 16,
                "width": viewer.FIG_SIZES["L"]["w"],
                "height": viewer.FIG_SIZES["L"]["h"],
            },
            "mini": {
                "ncols": 34,
                "nrows": 12,
                "width": viewer.FIG_SIZES["L2"]["w"],
                "height": viewer.FIG_SIZES["L2"]["h"],
            },
        }

    def _set_fields(self):
        # ------------ call super ----------- #
        super()._set_fields()
        # Attribute fields
        self.field_geometry = "geometry"
        # ... continues in downstream objects ... #

    def _set_view_specs(self):
        super()._set_view_specs()
        self.view_specs.update(
            {
                "subtitle_map": "Map",
                "ax_map": 0,
                "ax_data": 1,
                "ax_hist": 2,
                "ax_cdf": 3,
                "x_stats": 0.55,
                "zorder_map": 3,  # above polygons and lines of other layers
                "layers_map": None,  # list of other layers, see plot_map
                "empty_map": False,
                "grid_map": False,
                "marker_map": "o",
                "markersize_map": 10,
                "edgecolor_map": "none",
                "colorize_map": True,
                "cbar_scatter": True,
                "cbar_histh": True,
            }
        )
        return None

    def view(self, show=True, return_fig=False):
        """
        Get the visualization, with a map as the first panel.

        **Layouts**, set by ``view_specs["layout"]``:

        ========  ========================================================
        Layout    Panels
        ========  ========================================================
        ``full``  Map, data, histogram and CDF, with the statistics table.
        ``mini``  Map, data, histogram and CDF.
        ========  ========================================================

        **View specs**, set by ``view_specs[key] = value`` before the call:

        ====================  =================  =====================================================================================================================
        Key                   Default            Description
        ====================  =================  =====================================================================================================================
        ``style``             ``"wien"``         Name of the plot style. See :func:`plans.viewer.set_style`.
        ``folder``            auto               Folder of the saved figure.
        ``filename``          auto               Name of the saved figure, without extension.
        ``fig_format``        ``"jpg"``          Format of the saved figure.
        ``dpi``               ``300``            Resolution of the saved figure.
        ``title``             auto               Title of the figure.
        ``xvar``              auto               Not in use.
        ``yvar``              auto               Not in use.
        ``xlabel``            auto               Label of the x axis.
        ``ylabel``            auto               Label of the y axis.
        ``color``             ``"tab:grey"``     Color of the data.
        ``xmin``              None               Not in use.
        ``xmax``              None               Not in use.
        ``ymin``              None               Not in use.
        ``ymax``              None               Not in use.
        ``layout``            ``"full"``         Name of the layout. See the table of layouts.
        ``data_plot``         ``"scatter"``      Plot of the data panel: ``"scatter"`` or ``"boxplot"``.
        ``subtitle_data``     ``"Data Points"``  Title of the data panel. None hides it.
        ``subtitle_box``      ``"Boxplot"``      Title of the data panel, if a boxplot.
        ``subtitle_hist``     ``"Histogram"``    Title of the histogram. None hides it.
        ``subtitle_cdf``      ``"CDF"``          Title of the CDF. None hides it.
        ``subtitle_qq``       ``"Q-Q"``          Title of the Q-Q panel. None hides it.
        ``yvar_field``        auto               Column of values. Set with the data.
        ``xlabel_cdf``        ``"P(X)"``         Label of the x axis of the CDF.
        ``xlabel_qq``         auto               Label of the x axis of the Q-Q panel.
        ``data_label``        auto               Label of the data in the legend.
        ``data_legend``       ``False``          Show the legend of the data panel.
        ``color_hist``        ``"tab:grey"``     Color of the histogram.
        ``color_cdf``         ``"black"``        Color of the CDF.
        ``color_mean``        ``"red"``          Color of the mean line.
        ``color_mean_text``   None               Color of the mean label. None is black.
        ``scheme_cmap``       ``"equal"``        Classes of the color map: ``"equal"``, ``"quantiles"`` or other schemes of :func:`plans.stochastic.binning.get_bins`.
        ``n_classes_cmap``    ``5``              Number of classes of the color map.
        ``cmap``              ``"viridis"``      Name of the color map.
        ``alpha``             ``0.8``            Opacity of the data.
        ``alpha_hist``        ``1``              Opacity of the histogram.
        ``alpha_cdf``         ``1``              Opacity of the CDF.
        ``range``             None               Range of the y axis, as ``[low, high]``. None is set from the data.
        ``range_x``           None               Range of the x axis, as ``[low, high]``. None is set from the data.
        ``plot_mean``         ``True``           Show the mean line.
        ``plot_mean_data``    ``False``          Show the mean line also on the data panel.
        ``linestyle_mean``    ``"solid"``        Line style of the mean.
        ``pad_mean``          ``1``              Spaces between the mean label and its line.
        ``plot_mean_label``   ``True``           Show the mean label.
        ``hist_density``      ``True``           Not in use.
        ``bins``              ``20``             Number of histogram bins, or the width of the bins if ``bins_density``.
        ``bins_density``      ``False``          Take ``bins`` as the width of the bins.
        ``ax_data``           ``1``              Internal. Index of the data axis.
        ``ax_hist``           ``2``              Internal. Index of the histogram axis. False has no histogram.
        ``ax_cdf``            ``3``              Internal. Index of the CDF axis. False has no CDF.
        ``x_stats``           ``0.55``           Horizontal position of the statistics table, as a share of the figure.
        ``x_stats_sep``       ``0.2``            Space between columns of the statistics table.
        ``y_stats``           ``0.3``            Vertical position of the statistics table, as a share of the figure.
        ``zorder_data``       ``1``              Drawing order of the data.
        ``zorder_histh``      ``1``              Drawing order of the histogram.
        ``zorder_cdf``        ``1``              Drawing order of the CDF.
        ``scatter_factor``    ``4``              Size of the scatter markers.
        ``colorize_scatter``  ``False``          Color the scatter markers by the color map.
        ``box_width``         ``0.4``            Width of the boxplot.
        ``box_showfliers``    ``True``           Show the outliers of the boxplot.
        ``subtitle_map``      ``"Map"``          Title of the map. None hides it.
        ``ax_map``            ``0``              Internal. Index of the map axis.
        ``zorder_map``        ``3``              Drawing order of the data on the map.
        ``layers_map``        None               Other layers, as a list of dictionaries. See :meth:`plot_map`.
        ``empty_map``         ``False``          Hide the data on the map, leaving only other layers.
        ``grid_map``          ``False``          Show the grid of the map.
        ``marker_map``        ``"o"``            Marker of the points.
        ``markersize_map``    ``10``             Size of the points.
        ``edgecolor_map``     ``"none"``         Edge color of the points or polygons.
        ``colorize_map``      ``True``           Color the data on the map by the color map.
        ``cbar_scatter``      ``True``           Color the bar of the scatter panel. Off if ``colorize_scatter``.
        ``cbar_histh``        ``True``           Color the bars of the histogram by the color map.
        ``gs_*``              auto               Internal. Replaced by the shared grid of :mod:`plans.viewer`.
        ====================  =================  =====================================================================================================================

        :param show: option for showing instead of saving
        :type show: bool
        :param return_fig: option for returning the figure object
        :type return_fig: bool
        :return: figure object if ``return_fig`` is True, else None
        :rtype: :class:`matplotlib.figure.Figure` or None
        """
        return super().view(show=show, return_fig=return_fig)

    def load_data(self, file_data, layer_name, input_varfield=None):
        """
        Load data from file. Expected to overwrite superior methods.

        :param file_data: file path to data.
        :type file_data: str
        :param layer_name: name of the layer in the file
        :type layer_name: str
        :param input_varfield: [optional] name of the column of values.
            Default is the ``varfield`` attribute.
        :type input_varfield: str
        :return: None
        :rtype: None
        """
        # include geopandas
        import geopandas as gpd

        # -------------- overwrite relative path inputs -------------- #
        self.file_data = os.path.abspath(file_data)
        self.layer_name = layer_name

        # -------------- call loading function -------------- #
        s_key = self.varfield if input_varfield is None else input_varfield
        gdf = gpd.read_file(
            self.file_data, layer=layer_name, columns=[s_key, self.field_geometry]
        )

        # -------------- post-loading logic -------------- #
        self.set_data(input_df=gdf, input_varfield=s_key)

        # ... continues in downstream objects ... #

        return None

    def set_data(self, input_df, input_varfield=None):
        """
        Set data from a ``GeoDataFrame``, which is left untouched. Keeps only the
        values, as the ``varfield`` column, and the geometry. Rows with missing
        values are dropped.

        :param input_df: data with values and locations
        :type input_df: :class:`geopandas.GeoDataFrame`
        :param input_varfield: [optional] name of the column of values.
            Default is the ``varfield`` attribute.
        :type input_varfield: str
        :return: None
        :rtype: None
        """
        # include geopandas
        import geopandas as gpd

        s_key = self.varfield if input_varfield is None else input_varfield
        self.data = (
            gpd.GeoDataFrame(
                data={self.varfield: input_df[s_key].values},
                geometry=input_df.geometry.values,
                crs=input_df.crs,
            )
            .dropna()
            .reset_index(drop=True)
        )
        self.view_specs["yvar_field"] = self.varfield
        self.update()
        return None

    # todo [dev] -- export method

    @staticmethod
    def _build_axes(fig, gs, specs):
        # todo [docstring]
        # ------------ setup axes ------------
        if specs["layout"] == "full":
            fig.add_subplot(gs[2:15, 1:14])
            fig.add_subplot(gs[2:10, 16:20])
            fig.add_subplot(gs[2:10, 22:27])
            fig.add_subplot(gs[2:10, 29:])
        elif specs["layout"] == "mini":
            fig.add_subplot(gs[2:10, 1:9])
            fig.add_subplot(gs[2:10, 12:18])
            fig.add_subplot(gs[2:10, 20:26])
            fig.add_subplot(gs[2:10, 28:])
        return fig

    def _plot(self, fig, gs, specs):
        # todo [docstring]
        fig = super()._plot(fig=fig, gs=gs, specs=specs)

        all_axes = fig.get_axes()

        # ------------ map plot ------------
        ax_map = all_axes[specs["ax_map"]]

        self.plot_map(data=self.data, ax=ax_map, column=self.varfield, specs=specs)

        # ------------ scatter cbar plot ------------
        # handle plotting conflict
        if specs["colorize_scatter"]:
            specs["cbar_scatter"] = False
        if specs["cbar_scatter"]:
            Univar.plot_cbar(
                data=self.data[specs["yvar_field"]].values,
                ax=all_axes[specs["ax_data"]],
                scheme=specs["scheme_cmap"],
                cmap=specs["cmap"],
                n_classes=specs["n_classes_cmap"],
            )

        # ------------ hist cbar plot ------------
        if specs["cbar_histh"]:
            Univar.plot_cbar(
                data=self.data[specs["yvar_field"]].values,
                ax=all_axes[specs["ax_hist"]],
                scheme=specs["scheme_cmap"],
                cmap=specs["cmap"],
                n_classes=specs["n_classes_cmap"],
            )

        return fig

    @staticmethod
    def plot_map(data, ax, column, specs, legend=False):
        """
        Plot the data and other layers on the map panel.

        Other layers come from ``specs["layers_map"]``, as a list of dictionaries.
        The ``data`` key holds the geometries, in the same CRS as the data, and
        all other keys go to their ``plot`` method. For example,
        ``{"data": catchment, "facecolor": "none", "edgecolor": "black"}``.

        :param data: data to plot, left untouched
        :type data: :class:`geopandas.GeoDataFrame`
        :param ax: axis to plot on
        :type ax: :class:`matplotlib.axes.Axes`
        :param column: name of the column of values
        :type column: str
        :param specs: plot specification dictionary
        :type specs: dict
        :param legend: option to add a legend
        :type legend: bool
        :return: None
        :rtype: None
        """
        # square panel at the top left of its cell, for any map extent: the
        # map aspect widens the view limits instead of shrinking the panel
        ax.set_box_aspect(1)
        ax.set_anchor("NW")
        ax.set_adjustable("datalim")

        # other layers
        for dc_layer in specs["layers_map"] or []:
            dc_kwargs = {k: v for k, v in dc_layer.items() if k != "data"}
            dc_layer["data"].plot(ax=ax, **dc_kwargs)

        if not specs["empty_map"]:

            # handle scheme
            if specs["colorize_map"]:

                color_data = _binning.classify(
                    data=data[column].values,
                    n_classes=specs["n_classes_cmap"],
                    scheme=specs["scheme_cmap"],
                )
                color_cmap = viewer.get_discrete_cmap(
                    n_classes=specs["n_classes_cmap"], base_cmap_name=specs["cmap"]
                )

                data.plot(
                    ax=ax,
                    column=color_data,
                    zorder=specs["zorder_map"],
                    cmap=color_cmap,
                    legend=legend,
                    marker=specs["marker_map"],  # Use a circle marker for dots
                    markersize=specs[
                        "markersize_map"
                    ],  # Set the size of the points (adjust as needed)
                    edgecolor=specs["edgecolor_map"],
                )
            else:
                data.plot(
                    ax=ax,
                    column=column,
                    zorder=specs["zorder_map"],
                    cmap=specs["cmap"],
                    legend=legend,
                    marker=specs["marker_map"],  # Use a circle marker for dots
                    markersize=specs[
                        "markersize_map"
                    ],  # Set the size of the points (adjust as needed)
                    edgecolor=specs["edgecolor_map"],
                )
        # Set the Y-axis tick labels orientation
        ax.tick_params(
            axis="y",  # Apply to the y-axis
            labelrotation=90,  # Rotate labels by 90 degrees (vertical)
        )

        for label in ax.get_yticklabels():
            # Option A: Often looks good for vertical Y-labels on the left
            label.set_horizontalalignment("right")
            label.set_verticalalignment("center")
        if specs["subtitle_map"] is not None:
            ax.set_title(specs["subtitle_map"], loc="left")
        ax.grid(visible=specs["grid_map"])

        return None


class Bivar(DataSet):
    """
    The Bivariate object.

    Holds a paired ``x``/``y`` sample in a :class:`pandas.DataFrame`
    (sorted by ``x``) and supports fitting simple regression models
    (see ``models`` attribute) and assessing their errors.

    **Examples**

    .. code-block:: python

        from plans.datasets.analyst import Bivar

        bv = Bivar(name="StageDischarge", alias="SD")
        bv.set_data(x=vct_h, y=vct_q)
        bv.fit(model_type="Power")

        # scatter with marginal histograms
        bv.view(show=True)

        # model panel
        bv.view_specs["layout"] = "model"
        bv.view_specs["model_type"] = "Power"
        bv.view(show=True)

    """

    def __init__(self, name="MyBivar", alias="Bv0"):
        # ------------ set defaults ----------- #
        self.xfield = "x"
        self.yfield = "y"
        self.xname = "X"
        self.yname = "Y"
        self.xunits = "units"
        self.yunits = "units"

        # ------------ call super ----------- #
        super().__init__(name=name, alias=alias)

        # attributes
        self.x_min = None
        self.x_max = None
        self.y_min = None
        self.y_max = None

        # models setup
        # note: "Parameters" must match the function argument names
        self.models = {
            "Linear": {
                "Function": linear,
                "Formula": "f(x) = c0 + c1 * x",
                "Setup": pd.DataFrame(
                    {"Parameters": ["c0", "c1"], "Mean": [0.0, 1.0], "SD": [0.1, 0.1]}
                ),
                "Data": None,
                "Metrics": None,
            },
            "Power": {
                "Function": power,
                "Formula": "f(x) =  c2 * ((x + c0)^c1)",
                "Setup": pd.DataFrame(
                    {
                        "Parameters": ["c0", "c1", "c2"],
                        "Mean": [0.0, 1.0, 1.0],
                        "SD": [0.1, 0.1, 0.1],
                    }
                ),
                "Data": None,
                "Metrics": None,
            },
            "Power_zero": {
                "Function": power_zero,
                "Formula": "f(x) =  c1 * (x^c0)",
                "Setup": pd.DataFrame(
                    {"Parameters": ["c0", "c1"], "Mean": [1.0, 1.0], "SD": [0.1, 0.1]}
                ),
                "Data": None,
                "Metrics": None,
            },
        }
        # todo [dev] Gumbel model: f(x) = exp(-exp(-((x-a)/b)))

        self.layouts = {
            "full": {
                "ncols": 24,
                "nrows": 24,
                "width": viewer.FIG_SIZES["S"]["w"],
                "height": viewer.FIG_SIZES["S"]["h"],
            },
            "model": {  # square: three stacked panels
                "ncols": 24,
                "nrows": 24,
                "width": viewer.FIG_SIZES["M"]["w"],
                "height": viewer.FIG_SIZES["M"]["w"],
            },
            "default": {
                "ncols": 24,
                "nrows": 24,
                "width": viewer.FIG_SIZES["S"]["w"],
                "height": viewer.FIG_SIZES["S"]["h"],
            },
        }

    def _set_fields(self):
        """
        Set catalog fields names. Expected to increment superior methods.
        """
        # call super
        # ----------------------------------------------------------------
        super()._set_fields()

        # Bivar fields
        self.field_xunits = "xunits"
        self.field_yunits = "yunits"

    def get_metadata(self):
        """
        Get a dictionary with object metadata.
        Expected to increment superior methods.

        :return: dictionary with all metadata
        :rtype: dict
        """
        # call super
        dc_meta = super().get_metadata()

        # customize local metadata
        dc_meta_local = {
            self.field_xunits: self.xunits,
            self.field_yunits: self.yunits,
        }
        # update
        dc_meta.update(dc_meta_local)
        # move file_data to the end
        dc_meta.pop(self.field_file_data)
        dc_meta[self.field_file_data] = self.file_data
        return dc_meta

    def load_data(self, file_data, input_xfield=None, input_yfield=None, in_sep=";"):
        """
        Load data from file. Expected to overwrite superior methods.

        :param file_data: file path to data.
        :type file_data: str
        :param input_xfield: [optional] name of the x column in file. Default uses ``xfield``
        :type input_xfield: str
        :param input_yfield: [optional] name of the y column in file. Default uses ``yfield``
        :type input_yfield: str
        :param in_sep: column separator of file
        :type in_sep: str
        :return: None
        :rtype: None
        """
        # -------------- overwrite relative path inputs -------------- #
        self.file_data = os.path.abspath(file_data)

        # -------------- implement loading logic -------------- #
        s_xkey = self.xfield if input_xfield is None else input_xfield
        s_ykey = self.yfield if input_yfield is None else input_yfield

        default_columns = {
            s_xkey: float,
            s_ykey: float,
        }

        # -------------- call loading function -------------- #
        df = pd.read_csv(
            self.file_data,
            sep=in_sep,
            dtype=default_columns,
            usecols=list(default_columns.keys()),
        )

        # -------------- post-loading logic -------------- #
        df = df.rename(columns={s_xkey: self.xfield, s_ykey: self.yfield})
        self.data = self._clean_data(df=df)

        # -------------- update other mutables -------------- #
        self.update()

        return None

    def set_data(self, x, y):
        """
        Set paired arrays to data.

        :param x: array of x values
        :type x: :class:`numpy.ndarray`
        :param y: array of y values
        :type y: :class:`numpy.ndarray`
        :return: None
        :rtype: None
        """
        df = pd.DataFrame({self.xfield: x, self.yfield: y})
        self.data = self._clean_data(df=df)
        self.update()
        return None

    def _clean_data(self, df):
        """
        Drop missing pairs, sort by x and reset index.
        """
        df = df[[self.xfield, self.yfield]].dropna()
        return df.sort_values(by=self.xfield).reset_index(drop=True)

    def update(self):
        """
        Refresh mutable attributes based on data. Expected to increment superior methods.

        :return: None
        :rtype: None
        """
        # ------------ call super ----------- #
        super().update()

        # update stats
        if self.data is not None:
            self.x_min = self.data[self.xfield].min()
            self.x_max = self.data[self.xfield].max()
            self.y_min = self.data[self.yfield].min()
            self.y_max = self.data[self.yfield].max()

            # view specs
            self.view_specs["range_x"] = [self.x_min, self.x_max]
            self.view_specs["range"] = [self.y_min, self.y_max]

        return None

    # MODEL METHODS
    # ===================================================================

    def fit(self, model_type="Linear"):
        """
        Fit model to data using least squares.

        :param model_type: model type. Options: Linear, Power, Power_zero
        :type model_type: str
        :return: None
        :rtype: None
        """
        popt, pstd = _curves.fit_curve(
            func=self.models[model_type]["Function"],
            x=self.data[self.xfield].values,
            y=self.data[self.yfield].values,
            p0=self.models[model_type]["Setup"]["Mean"].values,
        )
        # update model
        self.update_model(params_mean=popt, params_sd=pstd, model_type=model_type)
        return None

    def update_model(self, params_mean, params_sd=None, model_type="Linear"):
        """
        Update model based on parameters.

        :param params_mean: mean of parameters
        :type params_mean: list
        :param params_sd: [optional] standard deviation of parameters
        :type params_sd: list
        :param model_type: model type. Options: Linear, Power, Power_zero
        :type model_type: str
        :return: None
        :rtype: None
        """
        # Setup
        self.models[model_type]["Setup"]["Mean"] = params_mean
        if params_sd is not None:
            self.models[model_type]["Setup"]["SD"] = params_sd
        # update sample
        self._update_model_data(model_type=model_type)
        # update model metrics
        df = self.models[model_type]["Data"]
        self.models[model_type]["Metrics"] = _metrics.get_metrics(
            observed=df[self.yfield].values,
            predicted=df[f"{self.yfield}_Mean"].values,
        )
        return None

    def _update_model_data(self, model_type="Linear"):
        """
        Update model predictions and errors (model minus observed) on data.
        """
        df_setup = self.models[model_type]["Setup"]
        dc_params = dict(zip(df_setup["Parameters"], df_setup["Mean"].values))
        df = self.data.copy()
        s_ymodel = f"{self.yfield}_Mean"
        # compute model on sample
        df[s_ymodel] = self.models[model_type]["Function"](
            x=df[self.xfield].values, **dc_params
        )
        # compute error
        df["e_Mean"] = df[s_ymodel] - df[self.yfield]
        # set attribute
        self.models[model_type]["Data"] = df
        return None

    # todo [dev] prediction bands via Monte Carlo simulation of fitted models

    # GET METHODS
    # ===================================================================

    def get_error_normality(self, model_type="Linear", clevel=0.95):
        """
        Get normality analysis of model errors using standard tests.

        :param model_type: model type. Options: Linear, Power, Power_zero
        :type model_type: str
        :param clevel: confidence level
        :type clevel: float
        :return: dataframe of assessment results
        :rtype: :class:`pandas.DataFrame`
        """
        self._update_model_data(model_type=model_type)
        uv = Univar(name=self.name)
        uv.set_array(array=self.models[model_type]["Data"]["e_Mean"].values)
        return uv.get_normality(clevel=clevel)

    # PLOT METHODS
    # ===================================================================

    def _set_view_specs(self):
        """
        Set view specifications. Expected to overwrite superior methods.

        :return: None
        :rtype: None
        """
        super()._set_view_specs()
        self.view_specs.update(
            {
                # layout
                "style": "wien",
                "layout": "full",
                "model_type": "Linear",
                # titles
                "subtitle_data": None,
                "subtitle_model": "Model",
                "subtitle_error": "Error",
                "subtitle_variance": "Error variance",
                "subtitle_qq": "Q-Q",
                # axis labels
                "xlabel": f"{self.xname} ({self.xunits})",
                "ylabel": f"{self.yname} ({self.yunits})",
                # colors
                "color": "tab:grey",
                "color_hist": "tab:grey",
                "color_model": "black",
                "color_error": "tab:grey",
                "color_variance": "darkred",
                "color_mean": "red",
                "color_mean_text": None,
                # alphas
                "alpha": 0.8,
                "alpha_hist": 1,
                "alpha_error": 0.8,
                # ranges
                "range": None,
                "range_x": None,
                "range_e": None,
                # mean
                "plot_mean": True,
                "linestyle_mean": "solid",
                "pad_mean": 1,
                "plot_mean_label": True,
                # histogram -- None bins uses Freedman-Diaconis rule
                "bins": None,
                "bins_density": False,
                # zorder
                "zorder_data": 1,
                "zorder_model": 2,
                "zorder_histh": 1,
            }
        )

        del self.view_specs["width"]
        del self.view_specs["height"]

        return None

    def _get_fig_specs(self):
        """
        Get figure specs by merging view specs, layout sizes and grid specs.
        """
        specs = self.view_specs.copy()

        # handle layout
        layout = specs["layout"]
        if layout not in self.layouts:
            raise ValueError(
                f"Unknown layout '{layout}'. Options: {list(self.layouts.keys())}"
            )

        # update sizes
        specs.update(self.layouts[layout].copy())

        # update gridspecs
        specs.update(viewer.GRID_SPECS)

        return specs

    def _build_axes(self, fig, gs, specs):
        """
        Add subplots to figure based on layout.
        """
        if specs["layout"] == "model":
            # left column stacked: model, error, variance (shared x)
            # 3-row gaps keep titles clear of the x labels above
            fig.add_subplot(gs[2:9, 3:14])  # 0: model
            fig.add_subplot(gs[19:23, 3:14])  # 1: error variance
            fig.add_subplot(gs[12:16, 3:14])  # 2: error
            fig.add_subplot(gs[12:16, 16:19])  # 3: error hist
            fig.add_subplot(gs[12:16, 21:24])  # 4: error qq
        else:
            fig.add_subplot(gs[8:21, 4:18])  # 0: scatter
            fig.add_subplot(gs[2:7, 4:18])  # 1: x hist
            fig.add_subplot(gs[8:21, 20:])  # 2: y hist
        return fig

    def _plot(self, fig, gs, specs):
        """
        Plot on figure based on layout.
        """
        # TITLE
        # -------------------------------------------------------------------
        if specs["title"] is not None:
            plt.suptitle(specs["title"], fontsize=9)

        # AXES
        # -------------------------------------------------------------------
        fig = self._build_axes(fig=fig, gs=gs, specs=specs)

        # PLOT
        # -------------------------------------------------------------------
        if specs["layout"] == "model":
            self._plot_model(fig=fig, specs=specs)
        else:
            self._plot_full(fig=fig, specs=specs)

        return fig

    def _plot_full(self, fig, specs):
        """
        Plot scatter with marginal histograms.
        """
        ax_data, ax_histx, ax_histy = fig.get_axes()
        vct_x = self.data[self.xfield].values
        vct_y = self.data[self.yfield].values

        # PLOT SCATTER
        # -------------------------------------------------------------------
        ax_data.scatter(
            vct_x,
            vct_y,
            marker=".",
            color=specs["color"],
            alpha=specs["alpha"],
            s=0.8 * viewer.MM_TO_PT,
            zorder=specs["zorder_data"],
        )
        if specs["subtitle_data"] is not None:
            ax_data.set_title(specs["subtitle_data"], loc="left")
        ax_data.set_xlim(specs["range_x"])
        ax_data.set_ylim(specs["range"])
        ax_data.set_xlabel(specs["xlabel"])
        ax_data.set_ylabel(specs["ylabel"])

        # PLOT X HIST
        # -------------------------------------------------------------------
        bins_x = specs["bins"]
        if bins_x is None:
            bins_x = _binning.get_nbins_fd(data=vct_x)
        ax_histx.hist(
            vct_x,
            bins=bins_x,
            color=specs["color_hist"],
            alpha=specs["alpha_hist"],
            weights=np.ones(len(vct_x)) / len(vct_x),
        )
        ax_histx.yaxis.set_major_formatter(mticker.PercentFormatter(1))
        ax_histx.set_xlim(specs["range_x"])
        ax_histx.tick_params(labelbottom=False)
        if specs["plot_mean"]:
            ax_histx.axvline(
                x=np.mean(vct_x),
                color=specs["color_mean"],
                linestyle=specs["linestyle_mean"],
            )
        # todo [DRY] consider a Univar.plot_histv counterpart of plot_histh

        # PLOT Y HIST
        # -------------------------------------------------------------------
        Univar.plot_histh(
            data=vct_y,
            ax=ax_histy,
            specs=self._get_histh_specs(specs=specs, data=vct_y),
        )
        ax_histy.tick_params(labelleft=False)

        return None

    def _plot_model(self, fig, specs):
        """
        Plot model panel: fit, error, error histogram, Q-Q and variance tracing.
        """
        ax_model, ax_var, ax_error, ax_ehist, ax_qq = fig.get_axes()

        # MODEL DATA
        # -------------------------------------------------------------------
        model_type = specs["model_type"]
        self._update_model_data(model_type=model_type)
        df_model = self.models[model_type]["Data"]
        vct_x = df_model[self.xfield].values
        vct_e = df_model["e_Mean"].values
        e_mean = np.mean(vct_e)

        # handle error range
        if specs["range_e"] is None:
            e_max = 1.5 * np.max(np.abs(vct_e))
            specs["range_e"] = [-e_max, e_max]

        # error ticks with explicit sign (e.g., +2)
        fmt_sign = mticker.FuncFormatter(
            lambda v, pos: "0" if v == 0 else "{:+g}".format(v)
        )

        # PLOT MODEL
        # -------------------------------------------------------------------
        ax_model.scatter(
            vct_x,
            df_model[self.yfield].values,
            marker=".",
            color=specs["color"],
            alpha=specs["alpha"],
            s=0.8 * viewer.MM_TO_PT,
            zorder=specs["zorder_data"],
        )
        ax_model.plot(
            vct_x,
            df_model[f"{self.yfield}_Mean"].values,
            color=specs["color_model"],
            linestyle="--",
            zorder=specs["zorder_model"],
        )
        if specs["subtitle_model"] is not None:
            ax_model.set_title(
                "{} ({})".format(specs["subtitle_model"], model_type), loc="left"
            )
        ax_model.set_xlim(specs["range_x"])
        ax_model.set_ylim(specs["range"])
        ax_model.set_xlabel(specs["xlabel"])
        ax_model.set_ylabel(specs["ylabel"])

        # PLOT VARIANCE TRACING
        # -------------------------------------------------------------------
        vct_var = _descriptive.trace_variance(data=vct_e)["Variance"].values
        ax_var.plot(vct_x, vct_var, color=specs["color_variance"])
        if specs["subtitle_variance"] is not None:
            ax_var.set_title(specs["subtitle_variance"], loc="left")
        ax_var.set_xlim(specs["range_x"])
        ax_var.set_ylim([0, 1.5 * np.max(vct_var)])
        ax_var.set_xlabel(specs["xlabel"])
        ax_var.set_ylabel(r"$\sigma^2$")

        # PLOT ERROR
        # -------------------------------------------------------------------
        ax_error.scatter(
            vct_x,
            vct_e,
            marker=".",
            color=specs["color_error"],
            alpha=specs["alpha_error"],
            s=0.8 * viewer.MM_TO_PT,
            zorder=specs["zorder_data"],
        )
        if specs["subtitle_error"] is not None:
            ax_error.set_title(specs["subtitle_error"], loc="left")
        ax_error.set_xlim(specs["range_x"])
        ax_error.set_ylim(specs["range_e"])
        ax_error.set_xlabel(specs["xlabel"])
        ax_error.set_ylabel(r"$\epsilon$")
        ax_error.yaxis.set_major_formatter(fmt_sign)
        if specs["plot_mean"]:
            Univar.plot_mean(
                ax=ax_error,
                y_mu=e_mean,
                xmin=specs["range_x"][0],
                xmax=specs["range_x"][1],
                specs=specs,
            )

        # PLOT ERROR HIST
        # -------------------------------------------------------------------
        specs_ehist = self._get_histh_specs(specs=specs, data=vct_e)
        specs_ehist["range"] = specs["range_e"]
        specs_ehist["plot_mean_label"] = False
        Univar.plot_histh(
            data=vct_e, ax=ax_ehist, specs=specs_ehist, formatter=fmt_sign
        )

        # PLOT ERROR QQ
        # -------------------------------------------------------------------
        df_qq = _descriptive.qqplot(data=vct_e)
        ax_qq.scatter(
            df_qq["T-Quantiles"],
            df_qq["Data"],
            marker=".",
            color=specs["color_error"],
            alpha=specs["alpha_error"],
            s=0.8 * viewer.MM_TO_PT,
        )
        if specs["subtitle_qq"] is not None:
            ax_qq.set_title(specs["subtitle_qq"], loc="left")
        ax_qq.set_ylim(specs["range_e"])
        ax_qq.set_xlabel("Normal quantiles")
        ax_qq.yaxis.set_major_formatter(fmt_sign)

        return None

    @staticmethod
    def _get_histh_specs(specs, data):
        """
        Get a specs copy suited for marginal ``Univar.plot_histh`` calls.
        """
        specs_h = specs.copy()
        specs_h["subtitle_hist"] = None
        specs_h["plot_mean_label"] = False
        if specs_h["bins"] is None:
            specs_h["bins"] = _binning.get_nbins_fd(data=data)
        return specs_h

    def view(self, show=True, return_fig=False):
        """
        Get the visualization. Layout is set by ``view_specs["layout"]``
        (``full`` or ``model``).

        **Layouts**, set by ``view_specs["layout"]``:

        ===========  ======================================================
        Layout       Panels
        ===========  ======================================================
        ``full``     Scatter with histograms on the sides.
        ``model``    Model, error, error histogram, Q-Q and error variance.
        ``default``  Same as ``full``.
        ===========  ======================================================

        **View specs**, set by ``view_specs[key] = value`` before the call:

        =====================  ==============  ==============================================================================
        Key                    Default         Description
        =====================  ==============  ==============================================================================
        ``style``              ``"wien"``      Name of the plot style. See :func:`plans.viewer.set_style`.
        ``folder``             auto            Folder of the saved figure.
        ``filename``           auto            Name of the saved figure, without extension.
        ``fig_format``         ``"jpg"``       Format of the saved figure.
        ``dpi``                ``300``         Resolution of the saved figure.
        ``title``              auto            Title of the figure.
        ``xvar``               auto            Not in use.
        ``yvar``               auto            Not in use.
        ``xlabel``             auto            Label of the x axis.
        ``ylabel``             auto            Label of the y axis.
        ``color``              ``"tab:grey"``  Color of the data.
        ``xmin``               None            Not in use.
        ``xmax``               None            Not in use.
        ``ymin``               None            Not in use.
        ``ymax``               None            Not in use.
        ``layout``             ``"full"``      Name of the layout. See the table of layouts.
        ``model_type``         ``"Linear"``    Model of the ``model`` layout: ``"Linear"``, ``"Power"`` or ``"Power_zero"``.
        ``subtitle_data``      None            Title of the scatter panel. None hides it.
        ``subtitle_model``     ``"Model"``     Title of the model panel. None hides it.
        ``subtitle_error``     ``"Error"``     Title of the error panel. None hides it.
        ``subtitle_variance``  auto            Title of the error variance panel. None hides it.
        ``subtitle_qq``        ``"Q-Q"``       Title of the Q-Q panel. None hides it.
        ``color_hist``         ``"tab:grey"``  Color of the histogram.
        ``color_model``        ``"black"``     Color of the model.
        ``color_error``        ``"tab:grey"``  Color of the errors.
        ``color_variance``     ``"darkred"``   Color of the error variance.
        ``color_mean``         ``"red"``       Color of the mean line.
        ``color_mean_text``    None            Color of the mean label. None is black.
        ``alpha``              ``0.8``         Opacity of the data.
        ``alpha_hist``         ``1``           Opacity of the histogram.
        ``alpha_error``        ``0.8``         Opacity of the errors.
        ``range``              None            Range of the y axis, as ``[low, high]``. None is set from the data.
        ``range_x``            None            Range of the x axis, as ``[low, high]``. None is set from the data.
        ``range_e``            None            Range of the errors, as ``[low, high]``. None is symmetric, set from the data.
        ``plot_mean``          ``True``        Show the mean line.
        ``linestyle_mean``     ``"solid"``     Line style of the mean.
        ``pad_mean``           ``1``           Spaces between the mean label and its line.
        ``plot_mean_label``    ``True``        Show the mean label.
        ``bins``               None            Number of histogram bins. None uses the Freedman-Diaconis rule.
        ``bins_density``       ``False``       Take ``bins`` as the width of the bins.
        ``zorder_data``        ``1``           Drawing order of the data.
        ``zorder_model``       ``2``           Drawing order of the model.
        ``zorder_histh``       ``1``           Drawing order of the histogram.
        ``gs_*``               auto            Internal. Replaced by the shared grid of :mod:`plans.viewer`.
        =====================  ==============  ==============================================================================

        :param show: option for showing instead of saving
        :type show: bool
        :param return_fig: option for returning the figure object
        :type return_fig: bool
        :return: figure object if ``return_fig`` is True, else None
        :rtype: :class:`matplotlib.figure.Figure` | None
        """
        # SPECS
        # -------------------------------------------------------------------
        specs = self._get_fig_specs()

        # BUILD
        # -------------------------------------------------------------------
        fig, gs = viewer.build_fig(specs=specs)

        # PLOT
        # -------------------------------------------------------------------
        fig = self._plot(fig=fig, gs=gs, specs=specs)

        # SHIP
        # -------------------------------------------------------------------
        file_path = "{}/{}.{}".format(
            specs["folder"], specs["filename"], specs["fig_format"]
        )
        if return_fig:
            return fig
        else:
            viewer.ship_fig(fig=fig, show=show, file_output=file_path, dpi=specs["dpi"])

    # STATIC METHODS
    # ===================================================================

    @staticmethod
    def get_metrics(observed, predicted):
        """Get all fit metrics. See :func:`plans.stochastic.metrics.get_metrics`."""
        return _metrics.get_metrics(observed=observed, predicted=predicted)

    @staticmethod
    def pearson(x, y):
        """Compute Pearson r. See :func:`plans.stochastic.metrics.pearson`."""
        return _metrics.pearson(x=x, y=y)

    @staticmethod
    def spearman(x, y):
        """Compute Spearman rho. See :func:`plans.stochastic.metrics.spearman`."""
        return _metrics.spearman(x=x, y=y)

    @staticmethod
    def rsq(observed, predicted):
        """Compute R2. See :func:`plans.stochastic.metrics.rsq`."""
        return _metrics.rsq(observed=observed, predicted=predicted)

    @staticmethod
    def rmse(observed, predicted):
        """Compute RMSE. See :func:`plans.stochastic.metrics.rmse`."""
        return _metrics.rmse(observed=observed, predicted=predicted)

    @staticmethod
    def mae(observed, predicted):
        """Compute MAE. See :func:`plans.stochastic.metrics.mae`."""
        return _metrics.mae(observed=observed, predicted=predicted)

    @staticmethod
    def bias(observed, predicted):
        """Compute Bias (%). See :func:`plans.stochastic.metrics.bias`."""
        return _metrics.bias(observed=observed, predicted=predicted)


# todo [upgrade] make it a child of some MbaE class
class Bayes:
    # todo [docstring] improve major docstring
    """
    The Bayes Theorem Analyst Object
    """

    def __init__(self, df_hypotheses, name="myBayes", nomenclature=None, gridsize=100):
        """Deploy the Bayes Analyst
        :param df_hypotheses: dataframe listing all model hypotheses. Must contain a field Name (of parameter), Min and Max.
        :type df_hypotheses: :class:pandas.DataFrame
        :param name: name of analyst
        :type name: str
        :param nomenclature: dictionary for rename nomenclature
        :type nomenclature: dict
        :param gridsize: grid resolution in histrograms (bins)
        :type gridsize: int
        """
        self.hypotheses = df_hypotheses
        # list of hypotheses by step
        self.bands = list()
        self.bands.append(self.hypotheses.copy())
        # other parameters
        self.name = name
        self.gridsize = gridsize

        # zero
        self.zero = 1 / gridsize

        # set labels
        self.shyp = "H"
        self.sevid = "E"
        self.sprior = "P(H)"
        self.slike = "P(E | H)"
        self.spost = "P(H | E)"
        self.saux = self.sprior + self.slike
        if nomenclature is not None:
            self._reset_nomenclature(dct_names=nomenclature)

        # set omega
        self.steps = list()
        # create step 0
        self._insert_new_step()

    def __str__(self):
        s1 = self.hypotheses.to_string()
        return s1

    def _reset_nomenclature(self, dct_names):
        """Reset nomenclature
        :param dct_names: dictionary to rename nomenclatures
        :type dct_names: dict
        :return: None
        :rtype: None
        """
        for k in dct_names:
            self.sevid = self.sevid.replace(k, dct_names[k])
            self.shyp = self.shyp.replace(k, dct_names[k])
            self.sprior = self.sprior.replace(k, dct_names[k])
            self.slike = self.slike.replace(k, dct_names[k])
            self.spost = self.spost.replace(k, dct_names[k])
            self.saux = self.sprior + self.slike

    def _insert_new_step(self):
        """convenience void function for inserting new step objects
        :return: None
        :rtype:
        """
        self.steps.append(dict())
        self.steps[len(self.steps) - 1]["Omega"] = dict()
        self.steps[len(self.steps) - 1]["Evidence"] = dict()
        self.steps[len(self.steps) - 1]["Bands"] = dict()
        for h in self.hypotheses["Name"].values:
            n_min = self.hypotheses.loc[self.hypotheses["Name"] == h, "Min"].values[0]
            n_max = self.hypotheses.loc[self.hypotheses["Name"] == h, "Max"].values[0]
            self.steps[len(self.steps) - 1]["Omega"][h] = pd.DataFrame(
                {
                    self.shyp: np.linspace(n_min, n_max, self.gridsize),
                    self.sprior: np.ones(self.gridsize) / self.gridsize,
                    self.slike: np.zeros(self.gridsize),
                    self.saux: np.zeros(self.gridsize),
                    self.spost: np.zeros(self.gridsize),
                }
            )
        return None

    def _accumulate(self, n_step):
        """convenience void function for accumulate probability
        :param n_step: step number to accumulate
        :type n_step: int
        :return: None
        :rtype: none
        """
        for h in self.hypotheses["Name"].values:
            df_omega = self.steps[n_step]["Omega"][h]
            for s in [self.sprior, self.slike, self.spost]:
                df_omega["{}_acc".format(s)] = _bayes.get_accumulated(
                    probabilities=df_omega[s].values
                )
        return None

    def conditionalize(self, dct_evidence, s_varfield="E", s_weightfield="W"):
        """Conditionalize procedure of the Bayes Theorem
        :param dct_evidence: base_object of evidence dataframes
        :type dct_evidence: dict
        :param s_varfield: name of variable field in evidence dataframes
        :type s_varfield: str
        :param s_weightfield: name of weights field in evidence dataframes
        :type s_weightfield: str
        :return: None
        :rtype: none
        """
        # instantiate new step
        n_step = len(self.steps)
        self._insert_new_step()

        # set evidence dict for step
        self.steps[n_step]["Evidence"] = dct_evidence

        # main loop
        for h in self.hypotheses["Name"].values:
            df_omega = self.steps[n_step]["Omega"][h]
            grid = df_omega[self.shyp].values

            # get prior from last step
            if n_step > 1:
                df_omega[self.sprior] = self.steps[n_step - 1]["Omega"][h][
                    self.spost
                ].values

            # get likelihood
            df_omega[self.slike] = _bayes.get_likelihood(
                evidence=dct_evidence[h][s_varfield],
                weights=dct_evidence[h][s_weightfield],
                grid=grid,
                baseline=self.zero,
            )

            # get posterior with Bayes Theorem
            df_omega[self.spost] = _bayes.get_posterior(
                prior=df_omega[self.sprior].values,
                likelihood=df_omega[self.slike].values,
            )

            # get accumulated values
            self._accumulate(n_step)

            # get 90% and 50% bands of accumulated
            self.steps[n_step]["Bands"][h] = dict()
            for s in [self.sprior, self.slike, self.spost]:
                acc = df_omega[s + "_acc"].values
                p05, p95 = _bayes.get_band(
                    grid=grid, accumulated=acc, lower=0.05, upper=0.95
                )
                p25, p75 = _bayes.get_band(
                    grid=grid, accumulated=acc, lower=0.25, upper=0.75
                )
                self.steps[n_step]["Bands"][h][s] = {
                    "p05": p05,
                    "p95": p95,
                    "p25": p25,
                    "p75": p75,
                }

        # return
        return None

    def plot_step(
        self,
        n_step,
        folder="C:/sample",
        filename="bayes",
        specs=None,
        dpi=300,
        show=False,
    ):
        """Void function for plot pannel of conditionalization step
        :param n_step: step number
        :type n_step: int
        :param folder: export folder
        :type folder: str
        :param filename: file name
        :type filename: str
        :param specs: plot specs base_object
        :type specs: dict
        :param dpi: plot resolution
        :type dpi: int
        :param show: control to show plot instead of saving
        :type show: bool
        :return: None
        :rtype: None
        """
        # get specs
        default_specs = {
            "color": "tab:grey",
            "title": "Conditionalization",
            "width": 10,
            "height": 5,
            "xlabel": "value",
            "range": (0, 1),
            "range_x": (0, 1),
            "subtitle": None,
        }
        # handle inputs specs
        if specs is None:
            pass
        else:  # override default
            for k in specs:
                default_specs[k] = specs[k]
        specs = default_specs

        # hunt some parameters
        lst_pmax = list()
        for h in self.hypotheses["Name"].values:  # get objects
            _df = self.steps[n_step]["Omega"][h]
            # get max p
            lst_pmax.append(
                np.max(
                    [
                        _df[self.sprior].max(),
                        _df[self.slike].max(),
                        _df[self.spost].max(),
                    ]
                )
            )
        n_pmax = 1.5 * np.max(lst_pmax)

        # main loop
        for h in self.hypotheses["Name"].values:
            specs["subtitle"] = "${}$".format(h)
            # get objects
            _df = self.steps[n_step]["Omega"][h]
            _bands = self.steps[n_step]["Bands"][h]

            # get width
            _wid = 0.7 * (_df[self.shyp].values[1] - _df[self.shyp].values[0])

            # get min max
            n_min = self.hypotheses.loc[self.hypotheses["Name"] == h, "Min"].values[0]
            n_max = self.hypotheses.loc[self.hypotheses["Name"] == h, "Max"].values[0]
            # start plot

            fig = plt.figure(figsize=(specs["width"], specs["height"]))  # Width, Height

            if specs["subtitle"] is None:
                plt.suptitle(specs["title"])
            else:
                plt.suptitle("{} | {}".format(specs["title"], specs["subtitle"]))
            # grid
            gs = mpl.gridspec.GridSpec(
                2, 3, wspace=0.4, hspace=0.5, left=0.1, bottom=0.1, top=0.85, right=0.95
            )  # nrows, ncols

            # grid loop
            lst_aux = [self.sprior, self.slike, self.spost]
            for i in range(len(lst_aux)):
                # Histogram
                ax = fig.add_subplot(gs[0, i])
                plt.title(lst_aux[i])
                plt.bar(
                    _df[self.shyp],
                    _df[lst_aux[i]],
                    width=_wid,
                    color=specs["color"],
                    align="edge",
                )
                plt.ylim(0, n_pmax)
                plt.xlim(n_min, n_max)
                plt.ylabel("$p({})$".format(h))
                plt.xlabel("${}$".format(h))
                # plt.gca().set_aspect(1 / (1.5))

                if i == 1:
                    # Accumulated
                    ax = fig.add_subplot(gs[1, i])
                    # plt.title(lst_aux[i])
                    plt.scatter(
                        self.steps[n_step]["Evidence"][h]["E"],
                        self.steps[n_step]["Evidence"][h]["W"],
                        marker=".",
                        c="k",
                        alpha=0.5,
                        linewidths=0.0,
                        edgecolors=None,
                    )
                    plt.xlim(n_min, n_max)
                    plt.ylabel("$W({})$".format(h))
                    plt.xlabel("${}$".format(h))
                    # plt.gca().set_aspect(1 / (1.5))
                else:
                    # Accumulated
                    ax = fig.add_subplot(gs[1, i])
                    # plt.title(lst_aux[i])
                    plt.plot(
                        _df[self.shyp],
                        _df["{}_acc".format(lst_aux[i])],
                        color="tab:blue",
                        zorder=3,
                    )
                    plt.fill_betweenx(
                        [-1, 2],
                        x1=self.steps[n_step]["Bands"][h][lst_aux[i]]["p25"],
                        x2=self.steps[n_step]["Bands"][h][lst_aux[i]]["p75"],
                        color="tab:grey",
                        alpha=0.5,
                        zorder=2,
                    )
                    plt.fill_betweenx(
                        [-1, 2],
                        x1=self.steps[n_step]["Bands"][h][lst_aux[i]]["p05"],
                        x2=self.steps[n_step]["Bands"][h][lst_aux[i]]["p95"],
                        color="tab:grey",
                        alpha=0.3,
                        zorder=1,
                    )
                    plt.ylim(-0.05, 1.05)
                    plt.xlim(n_min, n_max)
                    plt.ylabel("$P({})$".format(h))
                    plt.xlabel("${}$".format(h))
                    # plt.gca().set_aspect(1 / (1.5))

            # show or save
            if show:
                plt.show()
            else:
                plt.savefig(
                    "{}/{}_{}_step{}.png".format(folder, filename, h, n_step), dpi=dpi
                )

        # return
        return None


# ----- DEPRECATED CLASSES -----


if __name__ == "__main__":
    print("Hello world!")
