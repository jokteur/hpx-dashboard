import time

from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.events import Reset
import numpy as np
import pandas as pd
import xarray as xr
import datashader as ds
import datashader.transfer_functions as tf

from .base import BaseElement, ThrottledEvent, get_figure_options


def _is_intersecting(interval1, interval2):
    """"""
    return interval1[0] <= interval2[1] and interval2[0] <= interval1[1]


def _is_data_in_range(df, x_col, y_col, x_range=None, y_range=None):
    """"""
    if not len(df[x_col]) or not len(df[y_col]):
        return False

    if not isinstance(df, dict):
        df = pd.DataFrame(df)

    if x_range and y_range:
        idx_left = df[x_col].sub(x_range[0]).astype(float).abs().idxmin()
        idx_right = df[x_col].sub(x_range[1]).astype(float).abs().idxmin()
        if idx_left == idx_right:
            return False
        x_sub = df[x_col].loc[idx_left:idx_right]
        y_sub = df[y_col].loc[idx_left:idx_right]
        minx, miny = min(x_sub), min(y_sub)
        maxx, maxy = max(x_sub), max(y_sub)
        return _is_intersecting((minx, maxx), x_range) and _is_intersecting((miny, maxy), y_range)
    elif x_range:
        return _is_intersecting((min(df[x_col]), max(df[x_col])), x_range)
    elif y_range:
        return _is_intersecting((min(df[y_col]), max(df[y_col])), y_range)
    else:
        return True


def _normalize_ranges(x_range, y_range):
    """"""
    if x_range[0] == x_range[1]:
        x_range = (max(x_range[0] - 1.0, 0.0), x_range[0] + 1.0)
    if y_range[0] == y_range[1]:
        y_range = (max(y_range[0] - 1.0, 0.0), y_range[0] + 1.0)
    return x_range, y_range


def _compare_ranges(range1, range2, epsilon=1e-3):
    """Returns true if the both range are close enough (within epsilon)."""
    if not range1[0] or not range2[0]:
        return False
    return abs(range1[0] - range2[0]) < epsilon and abs(range1[1] - range2[1]) < epsilon


def shade(data, colors=None, **kwargs):
    """"""

    if "plot_width" not in kwargs or "plot_height" not in kwargs:
        raise ValueError("Please provide plot_width and plot_height for the canvas.")

    if isinstance(data, (list, tuple)) and isinstance(colors, (list, tuple)):
        if len(data) != len(colors):
            print(len(data), colors)
            raise ValueError("colors should have the same length as data.")

    if isinstance(data, (dict, pd.DataFrame)):
        data = [data]
    if colors and isinstance(colors, str):
        colors = [colors] * len(data)

    if "x_range" not in kwargs or "y_range" not in kwargs:
        x_range, y_range = get_ranges(data)
        if "x_range" not in kwargs:
            kwargs["x_range"] = x_range
        if "y_range" not in kwargs:
            kwargs["y_range"] = y_range

    kwargs["x_range"], kwargs["y_range"] = _normalize_ranges(kwargs["x_range"], kwargs["y_range"])

    cvs = ds.Canvas(**kwargs)
    aggs = []
    cs = []

    for i, line in enumerate(data):
        df = line
        if not isinstance(line, pd.DataFrame):
            df = pd.DataFrame(line).astype(float)

        plot = True
        if "x_range" in kwargs and "y_range" in kwargs:
            plot = _is_data_in_range(df, "x", "y", kwargs["x_range"], kwargs["y_range"])
        elif "x_range" in kwargs:
            plot = _is_data_in_range(df, "x", "y", kwargs["x_range"])
        elif "y_range" in kwargs:
            plot = _is_data_in_range(df, "x", "y", y_range=kwargs["y_range"])

        if len(df["x"]) == 0 or len(df["y"]) == 0:
            plot = False

        if plot:
            aggs.append(cvs.line(df, "x", "y"))
            if colors:
                cs.append(colors[i])

    if not aggs:
        return xr.DataArray(np.zeros((kwargs["plot_height"], kwargs["plot_width"]), dtype=int))
    if colors:
        imgs = [tf.shade(aggs[i], cmap=[c]) for i, c in enumerate(cs)]
        return tf.stack(*imgs)
    else:
        imgs = [tf.shade(aggs[i]) for i in range(len(data))]
        return tf.stack(*imgs)


def get_ranges(data):
    """"""

    finfo = np.finfo(float)
    x_range = (finfo.max, finfo.min)
    y_range = (finfo.max, finfo.min)

    if isinstance(data, (dict, pd.DataFrame)):
        data = [data]

    for line in data:
        if not len(line["x"]) or not len(line["y"]):
            continue
        x_range = (min(min(line["x"]), x_range[0]), max(max(line["x"]), x_range[1]))
        y_range = (min(min(line["y"]), y_range[0]), max(max(line["y"]), y_range[1]))

    if x_range[0] == y_range[0] == finfo.max or x_range[1] == y_range[0] == finfo.min:
        return (0.0, 1.0), (0.0, 1.0)
    return x_range, y_range


class ShadedTimeSeries(BaseElement):
    """"""

    # Variable to correctly update the range if necessary
    _keep_x_range = False
    _keep_y_range = False
    _last_reset = 0

    _num_update = 0

    def __init__(
        self,
        doc,
        data,
        colors=None,
        refresh_rate=500,
        **kwargs,
    ):
        """"""
        super().__init__(doc, refresh_rate)

        self._kwargs = kwargs
        self._throttledEvent = ThrottledEvent(doc, 50)

        # When the user resets the plot, sometimes the bokeh range has not been updated
        # before self._update() is called. self._update would then try to reset back the
        # interval to the previous state. The cooldown is to avoid this.
        self._cooldown_interval = refresh_rate * 2

        self._colors = colors
        self._data = data

        self._x_range, self._y_range = _normalize_ranges(*get_ranges(data))

        self._current_x_range, self._current_y_range = self._x_range, self._y_range

        self._defaults_opts = dict(plot_width=800, plot_height=300, title="")

        self._defaults_opts.update(
            (key, value) for key, value in kwargs.items() if key in get_figure_options()
        )

        if "x_range" in self._defaults_opts:
            self._current_x_range = self._defaults_opts["x_range"]
        if "y_range" in self._defaults_opts:
            self._current_y_range = self._defaults_opts["y_range"]

        img = shade(
            data,
            colors,
            plot_width=self._defaults_opts["plot_width"],
            plot_height=self._defaults_opts["plot_height"],
            x_range=self._current_x_range,
            y_range=self._current_y_range,
        )
        self._ds = ColumnDataSource(
            {
                "img": [img.values],
                "dw": [self._current_x_range[1] - self._current_x_range[0]],
                "dh": [self._current_y_range[1] - self._current_y_range[0]],
                "x": [self._current_x_range[0]],
                "y": [self._current_y_range[0]],
            }
        )

        self._root = figure(**self._defaults_opts)
        self._root.x_range.range_padding = self._root.y_range.range_padding = 0
        self._root.image_rgba(image="img", source=self._ds, x="x", y="y", dw="dw", dh="dh")
        self._root.on_event(Reset, self._reset_fct)

    def _reshade(self, immediate=False, message=""):
        """"""

        def gen():
            img = shade(
                self._data,
                self._colors,
                plot_width=self._defaults_opts["plot_width"],
                plot_height=self._defaults_opts["plot_height"],
                x_range=self._current_x_range,
                y_range=self._current_y_range,
            )
            self._ds.data = {
                "img": [img.values],
                "x": [self._current_x_range[0]],
                "y": [self._current_y_range[0]],
                "dw": [self._current_x_range[1] - self._current_x_range[0]],
                "dh": [self._current_y_range[1] - self._current_y_range[0]],
            }

        if immediate:
            gen()
        else:
            self._throttledEvent.add_event(gen)

    def _reset_fct(self, event):
        """"""
        self._x_range, self._y_range = _normalize_ranges(*get_ranges(self._data))
        self._current_x_range, self._current_y_range = self._x_range, self._y_range
        self._reshade()
        self._keep_x_range = self._keep_y_range = False
        self._last_reset = time.time()

    def update(self):
        """"""
        # Dirty hack because for some reason the plot range does not get
        # updated after the first update
        if self._num_update == 1:
            return

        if time.time() - self._last_reset < self._cooldown_interval / 1000:
            return

        # x_start = float(self._ds.data["x"][0])
        # x_end = float(x_start + self._ds.data["dw"][0])
        # y_start = float(self._ds.data["y"][0])
        # y_end = float(y_start + self._ds.data["dh"][0])

        # x_range = (self._root.x_range.start, self._root.x_range.end)
        # y_range = (self._root.y_range.start, self._root.y_range.end)

        # old_x_range = (x_start, x_end)
        # old_y_range = (y_start, y_end)

        # reshade = False

        # if not _compare_ranges(x_range, old_x_range) and self._root.x_range.start:
        #     self._current_x_range = x_range
        #     self._keep_x_range = True
        #     reshade = True

        # if not _compare_ranges(y_range, old_y_range) and self._root.y_range.start:
        #     self._current_y_range = y_range
        #     self._keep_y_range = True
        #     reshade = True

        # if reshade:
        #     self._reshade(True)

    def set_data(
        self,
        data,
        colors=None,
        x_range=None,
        y_range=None,
    ):
        """"""
        self._data = data

        _x_range, _y_range = _normalize_ranges(*get_ranges(data))

        if not self._keep_x_range:
            if x_range:
                self._current_x_range = x_range
            else:
                self._current_x_range = _x_range

        if not self._keep_y_range:
            if y_range:
                self._current_y_range = y_range
            else:
                self._current_y_range = _y_range

        if colors:
            self._colors = colors

        self._num_update += 1
        self._reshade(True)

    def set_range(self, x_range=None, y_range=None):
        if x_range:
            self._current_x_range = y_range
        if y_range:
            self._current_y_range = y_range
        self._reshade()
