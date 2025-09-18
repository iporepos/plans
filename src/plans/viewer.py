# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Functions designed to handle plots.

Overview
--------

# todo [major docstring improvement] -- overview
Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl. Pellentesque habitant morbi tristique senectus
et netus et malesuada fames ac turpis egestas.

Example
-------

# todo [major docstring improvement] -- examples
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam,
in porttitor lacus lobortis vitae. In a lacinia nisl.

.. code-block:: python

    import numpy as np
    from plans import viewer

    # view sample
    uni.view()

Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl.

"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# Define a conversion factor from mm to points
MM_TO_PT = 2.83465


FIG_SIZES = {
    "S": {
        "w": 81,
        "h": 80,
    },
    "M": {
        "w": 120,
        "h": 80,
    },
    "M2": {
        "w": 120,
        "h": 60,
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
    "gs_left": 0.01,
    "gs_right": 0.98,
    "gs_top": 0.98,
    "gs_bottom": 0.02,
}


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
    },
}


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
    plt.rcParams["font.sans-serif"] = ["Arial"]
    # Font sizes

    # Desired font sizes in millimeters
    tick_label_size_mm = 2.2
    axis_label_size_mm = 2.52  # Example: 5 mm for axis labels
    title_size_mm = 2.78  # Example: 6.5 mm for title
    # Convert mm to points
    tick_label_size_pt = tick_label_size_mm * MM_TO_PT
    axis_label_size_pt = axis_label_size_mm * MM_TO_PT
    title_size_pt = title_size_mm * MM_TO_PT
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
    plt.rcParams["xtick.major.pad"] = MM_TO_PT
    plt.rcParams["ytick.major.pad"] = MM_TO_PT

    # You might also want to set global tick length and width if not already
    plt.rcParams["xtick.major.size"] = MM_TO_PT  # Default is 3.5, adjust as needed
    plt.rcParams["ytick.major.size"] = MM_TO_PT
    plt.rcParams["xtick.major.width"] = FIG_STYLES[style][
        "lines_w"
    ]  # Default is 0.8, adjust as needed
    plt.rcParams["ytick.major.width"] = FIG_STYLES[style]["lines_w"]

    # Axes
    plt.rcParams["axes.linewidth"] = FIG_STYLES[style]["lines_w"]
    plt.rcParams["axes.labelpad"] = MM_TO_PT
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
    colors = [base_cmap(i / (n_classes - 1)) for i in range(n_classes)]
    # get custom ok new
    custom_cmap = mcolors.ListedColormap(colors)
    return custom_cmap
