# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Handle plots in ``matplotlib``

Call constants and functions from this module in order
to built plots with ``matplotlib``.

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
import matplotlib as mpl
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.artist as martist
import matplotlib.collections as mcollections
import matplotlib.colors as mcolors
import matplotlib.ticker as mticker

# ... {develop}

# Project-level imports
# =======================================================================
# import {module}
# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# Define a conversion factor from mm to points
MM_TO_PT = 2.83465

LABEL_SIZE_TICK = 2.2  # mm
LABEL_SIZE_AXIS = 2.52  # mm
LABEL_SIZE_TITLE = 2.78  # mm

# screen resolution (inline and windows) -- saving uses its own dpi
FIG_DPI = 150


FIG_SIZES = {
    "S": {
        "w": 81,
        "h": 80,
    },
    "S2": {
        "w": 81,
        "h": 30,
    },
    "M": {
        "w": 120,
        "h": 80,
    },
    "M2": {
        "w": 120,
        "h": 60,
    },
    "M3": {
        "w": 120,
        "h": 30,
    },
    "L": {
        "w": 170,
        "h": 80,
    },
    "L2": {
        "w": 170,
        "h": 60,
    },
}


GRID_SPECS = {
    "gs_wspace": 0.05,
    "gs_hspace": 0.05,
    "gs_left": 0.02,
    "gs_right": 0.98,
    "gs_top": 0.98,
    "gs_bottom": 0.06,
}


# drawing order of the layers of a panel. Images stay at 0 and plots start at 1
ZORDER_GRID = 0.25
ZORDER_FRAME = 100

COLOR_ANNOTATION = "#5f5f5f"

FIG_STYLES = {
    "bare": {
        "lines_w": 0.22 * MM_TO_PT,
        "lines_frame": "black",
        "lines_grids": "gray",
        "labels_ticks": "black",
        "labels_axes": "black",
        "labels_titles": "black",
        "background_axes": "white",
        "background_fig": "white",
        "grid": True,
        "label_pad": 1.0 * MM_TO_PT,
    },
    "wien": {
        "lines_w": 0.22 * MM_TO_PT,
        "lines_frame": "black",
        "lines_grids": "white",
        "labels_ticks": "black",
        "labels_axes": "black",
        "labels_titles": "black",
        "background_axes": "f6f7f9ff",  # f4f4faff; e5e5ecff, eeedf3ff
        "background_fig": "white",
        "grid": True,
        "label_pad": 1.2 * MM_TO_PT,
    },
    "wien3d": {
        "lines_w": 0.22 * MM_TO_PT,
        "lines_frame": "black",
        "lines_grids": "white",
        "labels_ticks": "black",
        "labels_axes": "black",
        "labels_titles": "black",
        "background_axes": "white",  # f4f4faff; e5e5ecff, eeedf3ff
        "background_fig": "white",
        "grid": True,
        "label_pad": 1.0 * MM_TO_PT,
    },
    "wien-light": {
        "lines_w": 0.22 * MM_TO_PT,
        "lines_frame": "black",
        "lines_grids": "gray",
        "labels_ticks": "black",
        "labels_axes": "black",
        "labels_titles": "black",
        "background_axes": "white",
        "background_fig": "white",
        "grid": True,
        "label_pad": 1.1 * MM_TO_PT,
    },
    "wien-clean": {
        "lines_w": 0.22 * MM_TO_PT,
        "lines_frame": "black",
        "lines_grids": "gray",
        "labels_ticks": "black",
        "labels_axes": "black",
        "labels_titles": "black",
        "background_axes": "white",
        "background_fig": "white",
        "grid": False,
        "label_pad": 1.1 * MM_TO_PT,
    },
    "seaborn": {
        "lines_w": 0.0 * MM_TO_PT,
        "lines_frame": "black",
        "lines_grids": "white",
        "labels_ticks": "333333ff",
        "labels_axes": "black",
        "labels_titles": "black",
        "background_axes": "ebebffff",
        "background_fig": "white",
        "grid": True,
        "label_pad": 1.0 * MM_TO_PT,
    },
    "dark": {
        "lines_w": 0.22 * MM_TO_PT,
        "lines_frame": "white",
        "lines_grids": "gray",
        "labels_ticks": "whitesmoke",
        "labels_axes": "white",
        "labels_titles": "white",
        "background_axes": "black",
        "background_fig": "black",
        "grid": True,
        "label_pad": 1.0 * MM_TO_PT,
    },
}

# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================


def set_figsize(width_mm, height_mm):
    """
    Sets the figure size in millimeters.

    :param width_mm: The width of the figure in millimeters.
    :type width_mm: float
    :param height_mm: The height of the figure in millimeters.
    :type height_mm: float
    """
    plt.rcParams["figure.figsize"] = [width_mm / 25.4, height_mm / 25.4]
    return None


def set_style(style=None):
    """
    Sets the viwer style. options: bare, dark, seaborn, wien, wien-light, wien-clean

    :param style: [optional] The style of the fonts. Default value = "bare"
    :type style: str
    """
    set_frame(style=style)
    set_fonts(style=style)
    set_colors(style=style)
    return None


def set_fonts(style=None):
    """
    Sets the font styles and sizes for plots.

    :param style: [optional] The style of the fonts. Default value = "bare"
    :type style: str
    """
    if style is None:
        style = "bare"
    # Font style
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.serif"] = ["Times New Roman"]
    # DejaVu Sans ships with matplotlib, for systems without Arial
    plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans"]
    # Font sizes

    # Convert mm to points
    tick_label_size_pt = LABEL_SIZE_TICK * MM_TO_PT
    axis_label_size_pt = LABEL_SIZE_AXIS * MM_TO_PT
    title_size_pt = LABEL_SIZE_TITLE * MM_TO_PT

    plt.rcParams["font.size"] = tick_label_size_pt
    plt.rcParams["xtick.labelsize"] = tick_label_size_pt
    plt.rcParams["ytick.labelsize"] = tick_label_size_pt
    plt.rcParams["axes.labelsize"] = axis_label_size_pt
    plt.rcParams["axes.titlesize"] = title_size_pt
    return None


def set_frame(style=None):
    """
    Sets the frame style, including ticks, tick labels, axes, and grid.

    :param style: [optional] The style of the frame. Default value = "bare"
    :type style: str
    """
    if style is None:
        style = "bare"
    # Tick direction: 'in' for ticks inside the plot frame
    plt.rcParams["xtick.direction"] = "in"
    plt.rcParams["ytick.direction"] = "in"

    # Tick label padding (distance from tick to label)
    # This applies globally to all major ticks
    plt.rcParams["xtick.major.pad"] = FIG_STYLES[style]["label_pad"]
    plt.rcParams["ytick.major.pad"] = FIG_STYLES[style]["label_pad"]

    # You might also want to set global tick length and width if not already
    plt.rcParams["xtick.major.size"] = MM_TO_PT  # Default is 3.5, adjust as needed
    plt.rcParams["ytick.major.size"] = MM_TO_PT
    plt.rcParams["xtick.major.width"] = FIG_STYLES[style][
        "lines_w"
    ]  # Default is 0.8, adjust as needed
    plt.rcParams["ytick.major.width"] = FIG_STYLES[style]["lines_w"]

    # Axes
    plt.rcParams["axes.linewidth"] = FIG_STYLES[style]["lines_w"]
    plt.rcParams["axes.labelpad"] = FIG_STYLES[style]["label_pad"]

    # grids
    plt.rcParams["grid.linewidth"] = 0.16 * MM_TO_PT  # Width of gridlines
    plt.rcParams["grid.linestyle"] = (
        "-"  # Style of gridlines (e.g., '-', '--', ':', '-.')
    )
    # --- Set gridlines to appear in the background ---
    plt.rcParams["axes.axisbelow"] = True
    plt.rcParams["axes.grid"] = FIG_STYLES[style]["grid"]

    # Plot lines
    # Set the default line width for all lines
    plt.rcParams["lines.linewidth"] = 0.35 * MM_TO_PT  # Default linewidth for all lines

    # allow only built-in math mode
    plt.rcParams["text.usetex"] = False
    return None


def set_colors(style=None):
    """
    Sets the color scheme for the plot, including figure background, axes background, grid, lines, and text.

    :param style: [optional] The color style to apply. Default value = "bare"
    :type style: str
    """
    if style is None:
        style = "bare"
    plt.rcParams["savefig.facecolor"] = FIG_STYLES[style]["background_fig"]
    plt.rcParams["figure.facecolor"] = FIG_STYLES[style]["background_fig"]
    plt.rcParams["axes.facecolor"] = FIG_STYLES[style]["background_axes"]
    plt.rcParams["grid.color"] = FIG_STYLES[style]["lines_grids"]  # Color of gridlines
    plt.rcParams["grid.alpha"] = 1.0  # Transparency of gridlines (0.0 to 1.0)

    # Set axis lines (spines) color
    plt.rcParams["axes.edgecolor"] = FIG_STYLES[style][
        "lines_frame"
    ]  # Color of the plot frame/border

    # Set tick lines color
    plt.rcParams["xtick.color"] = FIG_STYLES[style][
        "lines_frame"
    ]  # Color of x-axis tick marks
    plt.rcParams["ytick.color"] = FIG_STYLES[style][
        "lines_frame"
    ]  # Color of y-axis tick marks

    # Set font colors for various text elements
    plt.rcParams["text.color"] = FIG_STYLES[style][
        "labels_titles"
    ]  # Default text color for titles, legends etc.
    plt.rcParams["axes.labelcolor"] = FIG_STYLES[style][
        "labels_axes"
    ]  # Color of axis labels (xlabel, ylabel)
    plt.rcParams["xtick.labelcolor"] = FIG_STYLES[style][
        "labels_ticks"
    ]  # Color of x-axis tick labels
    plt.rcParams["ytick.labelcolor"] = FIG_STYLES[style][
        "labels_ticks"
    ]  # Color of y-axis tick labels
    return None


def build_fig(specs):
    """
    Builds a matplotlib figure and GridSpec object based on the given specifications.

    :param specs: A dictionary containing the specifications for the figure and GridSpec.
                  It should include 'width', 'height', 'nrows', 'ncols', 'gs_wspace',
                  'gs_hspace', 'gs_left', 'gs_right', 'gs_bottom', 'gs_top', and optionally 'style'.
    :type specs: dict
    :return: A tuple containing the matplotlib figure and GridSpec object.
    :rtype: tuple[:class:`matplotlib.figure.Figure`, :class:`matplotlib.gridspec.GridSpec`]
    """
    # handle missing style
    if "style" not in specs.keys():
        specs["style"] = None

    # start plot and apply style
    set_figsize(width_mm=specs["width"], height_mm=specs["height"])
    plt.rcParams["figure.dpi"] = FIG_DPI

    # set style
    set_style(style=specs["style"])

    # instantiate figure
    fig = plt.figure()  # Width, Height

    # get a grid specs
    gs = mpl.gridspec.GridSpec(
        specs["nrows"],  # rows
        specs["ncols"],  # columns
        wspace=specs["gs_wspace"],
        hspace=specs["gs_hspace"],
        left=specs["gs_left"],
        right=specs["gs_right"],
        bottom=specs["gs_bottom"],
        top=specs["gs_top"],
    )
    return fig, gs


def ship_fig(fig, show=True, file_output=None, dpi=300):
    """
    Handles the output of a matplotlib figure, either by showing it or saving it to a file.

    :param fig: The matplotlib figure to be handled.
    :type fig: :class:`matplotlib.figure.Figure`
    :param show: Whether to display the figure. Default value = True
    :type show: bool
    :param file_output: [optional] The file path to save the figure. If None, the figure is not saved.
    :type file_output: str
    :param dpi: The dots per inch for saving the figure. Default value = 300
    :type dpi: int
    :return: None if `show` or `file_output` is true, or the figure object if `return_fig` is true.
    :rtype: :class:`matplotlib.figure.Figure` or None
    """
    if show:
        plt.show()
        return None
    elif file_output is not None:
        fig.savefig(file_output, dpi=dpi)
        plt.close(fig)
        return None
    else:
        return None


def clear_xticks(axes):
    """
    Lower the y axis when a y grid line would cross the inward x ticks.

    Matplotlib draws each axis grid and ticks together, the y axis last, so a
    y grid line close to the bottom always covers the x ticks. A grid line right
    at the bottom is hidden by the frame, so it stays.

    :param axes: axes with the same y limits and height
    :type axes: list
    :return: None
    :rtype: None
    """
    ax = axes[0]
    trans = ax.get_yaxis_transform()
    pt_to_px = ax.figure.dpi / 72
    px_clear = pt_to_px * (
        plt.rcParams["xtick.major.size"] + 0.5 * plt.rcParams["grid.linewidth"]
    )
    px_frame = pt_to_px * 0.5 * plt.rcParams["axes.linewidth"]

    # new limits may bring new ticks
    for _ in range(3):
        y0, y1 = ax.get_ylim()
        px_bottom = trans.transform((0, y0))[1]
        ls_px = [trans.transform((0, y))[1] for y in ax.get_yticks() if y0 < y < y1]
        ls_close = [px for px in ls_px if px_frame < px - px_bottom < px_clear]
        if len(ls_close) == 0:
            break
        y_new = trans.inverted().transform((0, max(ls_close) - px_clear))[1]
        for a in axes:
            a.set_ylim(bottom=y_new)
    return None


def get_annotation_specs():
    """
    Get the style of annotations, such as statistics and values inside a panel.

    :return: arguments of a text
    :rtype: dict
    """
    return {"color": COLOR_ANNOTATION, "fontsize": plt.rcParams["font.size"] - 1}


class CoordinateLocator(mticker.Locator):
    """
    Locator of a fixed number of round ticks inside the view, for map coordinates.
    """

    def __init__(self, n_ticks=3):
        self.n_ticks = n_ticks

    def __call__(self):
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin=vmin, vmax=vmax)

    def tick_values(self, vmin, vmax):
        """
        Get the ticks of a view.

        :param vmin: lower limit of the view
        :type vmin: float
        :param vmax: upper limit of the view
        :type vmax: float
        :return: ticks
        :rtype: :class:`numpy.ndarray`
        """
        vmin, vmax = sorted([vmin, vmax])
        if vmin == vmax or self.n_ticks < 2:
            return np.array([(vmin + vmax) / 2])
        n_mid = (vmin + vmax) / 2
        n_range = vmax - vmin

        # largest round step that keeps the ticks away from the frame
        n_max_step = 0.8 * n_range / (self.n_ticks - 1)
        n_scale = 10 ** np.floor(np.log10(n_max_step))
        n_step = max(n * n_scale for n in [1, 2, 5] if n * n_scale <= n_max_step)

        # coarsest snap of the center that leaves the ticks nearly centered
        n_power = np.floor(np.log10(n_step))
        n_center = np.round(n_mid / 10**n_power) * 10**n_power
        while abs(n_center - n_mid) > 0.1 * n_range:
            n_power = n_power - 1
            n_center = np.round(n_mid / 10**n_power) * 10**n_power

        vct_ticks = n_center + n_step * (
            np.arange(self.n_ticks) - (self.n_ticks - 1) / 2
        )
        # keep the ticks free of floating point residues
        n_decimals = int(max(0, 1 - min(n_power, np.floor(np.log10(n_step)))))
        return np.round(vct_ticks, n_decimals)


class AxisGrid(martist.Artist):
    """
    Grid lines of one axis, as an artist with its own drawing order. An axis draws
    its ticks and its grid together, so they can not be on different layers.
    """

    def __init__(self, axis, gridline):
        """
        Initialize the grid.

        :param axis: axis to follow, for the positions of the lines
        :type axis: :class:`matplotlib.axis.Axis`
        :param gridline: line to copy the style from
        :type gridline: :class:`matplotlib.lines.Line2D`
        """
        super().__init__()
        self.axis = axis
        self.lines = mcollections.LineCollection(
            segments=[],
            colors=[gridline.get_color()],
            linewidths=gridline.get_linewidth(),
            linestyles=gridline.get_linestyle(),
            alpha=gridline.get_alpha(),
        )
        self.set_zorder(ZORDER_GRID)
        self.set_in_layout(False)

    def draw(self, renderer):
        """
        Draw the lines at the current ticks of the axis.

        :param renderer: renderer of the figure
        :type renderer: :class:`matplotlib.backend_bases.RendererBase`
        :return: None
        :rtype: None
        """
        ax = self.axes
        n_low, n_high = sorted(self.axis.get_view_interval())
        ls_ticks = [v for v in self.axis.get_majorticklocs() if n_low <= v <= n_high]
        if self.axis.axis_name == "x":
            self.lines.set_segments([[(v, 0), (v, 1)] for v in ls_ticks])
            self.lines.set_transform(ax.get_xaxis_transform())
        else:
            self.lines.set_segments([[(0, v), (1, v)] for v in ls_ticks])
            self.lines.set_transform(ax.get_yaxis_transform())
        self.lines.set_figure(ax.figure)
        self.lines.set_clip_path(ax.patch)
        self.lines.draw(renderer)
        self.stale = False
        return None


def set_layers(fig):
    """
    Set the drawing order of all panels of a figure. From the bottom to the top:
    background, raster, grid, plot elements (with their own order), ticks and frame.

    :param fig: figure with all panels already plotted
    :type fig: :class:`matplotlib.figure.Figure`
    :return: None
    :rtype: None
    """
    for ax in fig.get_axes():
        for axis in [ax.xaxis, ax.yaxis]:
            ls_gridlines = axis.get_gridlines()
            if len(ls_gridlines) > 0 and ls_gridlines[0].get_visible():
                ax.add_artist(AxisGrid(axis=axis, gridline=ls_gridlines[0]))
                axis.grid(visible=False)
            axis.set_zorder(ZORDER_FRAME)
        for spine in ax.spines.values():
            spine.set_zorder(ZORDER_FRAME)
    return None


def get_discrete_cmap(n_classes, base_cmap_name="viridis"):
    """
    Creates a colormap suitable for plotting classification.

    :param n_classes: The number of classes.
    :type n_classes: int
    :param base_cmap_name: The name of the base Matplotlib colormap. Defaults to 'viridis'.
    :type base_cmap_name: str, optional
    :returns: A custom colormap.
    :rtype: matplotlib.colors.ListedColormap
    """
    base_cmap = plt.get_cmap(base_cmap_name)  # Get colormap by name
    divider = n_classes - 1
    if n_classes <= 1:
        divider = 1

    colors = [base_cmap(i / (divider)) for i in range(n_classes)]
    # get custom ok new
    custom_cmap = mcolors.ListedColormap(colors)
    return custom_cmap


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    print("Hello world!")
    # ... {develop}
