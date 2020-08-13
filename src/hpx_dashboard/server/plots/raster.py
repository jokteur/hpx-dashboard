from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.events import Reset
import numpy as np
import pandas as pd
import xarray as xr
import datashader as ds
import datashader.transfer_functions as tf

from .base import BasePlot, ThrottledEvent, get_figure_options


def _is_intersecting(interval1, interval2):
    """"""
    return interval1[0] <= interval2[1] and interval2[0] <= interval1[1]


def _is_data_in_range(df, x_col, y_col, x_range=None, y_range=None):
    """"""
    if not len(df[x_col]) or not len(df[y_col]):
        return False

    if x_range and y_range:
        idx_left = df[x_col].sub(x_range[0]).astype(float).abs().idxmin()
        idx_right = df[x_col].sub(x_range[1]).astype(float).abs().idxmin()
        if idx_left == idx_right:
            return False
        minx, miny = min(df[x_col][idx_left:idx_right]), min(df[y_col][idx_left:idx_right])
        maxx, maxy = max(df[x_col][idx_left:idx_right]), max(df[y_col][idx_left:idx_right])
        return _is_intersecting((minx, maxx), x_range) and _is_intersecting((miny, maxy), y_range)
    elif x_range:
        return _is_intersecting((min(df[x_col]), max(df[x_col])), x_range)
    elif y_range:
        return _is_intersecting((min(df[y_col]), max(df[y_col])), y_range)
    else:
        return True


def shade(data, x, y, colors=None, **kwargs):
    """"""

    if "plot_width" not in kwargs or "plot_height" not in kwargs:
        raise ValueError("Please provide plot_width and plot_height for the canvas.")

    if isinstance(y, (list, tuple)) and isinstance(x, str):
        x = [x] * len(y)

    if isinstance(y, str):
        if isinstance(x, list):
            raise ValueError("If y is an str, then x should also be a str.")
        else:
            x = [x]
        y = [y]

    if len(x) != len(y):
        raise ValueError("x and y should be the same length.")

    if isinstance(colors, (list, tuple)):
        if len(colors) != len(y):
            raise ValueError("colors should have the same length as y.")
    elif isinstance(colors, str):
        colors = [colors] * len(y)

    if kwargs["x_range"][0] == kwargs["x_range"][1]:
        kwargs["x_range"] = (kwargs["x_range"][0] - 1, kwargs["x_range"][0] + 1)
    if kwargs["y_range"][0] == kwargs["y_range"][1]:
        kwargs["y_range"] = (kwargs["y_range"][0] - 1, kwargs["y_range"][0] + 1)

    cvs = ds.Canvas(**kwargs)
    aggs = []
    cs = []
    if isinstance(data, (dict, pd.DataFrame)):
        df = data
        if not isinstance(data, pd.DataFrame):
            df = pd.DataFrame(data).astype(float)

        for x, y, c in list(zip(x, y, colors)):
            plot = True
            if "x_range" in kwargs and "y_range" in kwargs:
                plot = _is_data_in_range(df, x, y, kwargs["x_range"], kwargs["y_range"])
            elif "x_range" in kwargs:
                plot = _is_data_in_range(df, x, y, kwargs["x_range"])
            elif "y_range" in kwargs:
                plot = _is_data_in_range(df, x, y, y_range=kwargs["y_range"])

            if len(df[x]) == 0 or len(df[y]) == 0:
                plot = False

            if plot:
                aggs.append(cvs.line(df, x, y) for (x, y) in list(zip(x, y)))
                if colors:
                    cs.append(c)
    elif isinstance(data, (list, tuple)):
        if len(y) != len(data):
            raise ValueError(
                "When data is supplied as a list or tuple "
                "then y and data should be the same length."
            )
        for i, line in enumerate(data):
            df = line
            if not isinstance(line, pd.DataFrame):
                df = pd.DataFrame(line).astype(float)

            plot = True
            if "x_range" in kwargs and "y_range" in kwargs:
                plot = _is_data_in_range(df, x[i], y[i], kwargs["x_range"], kwargs["y_range"])
            elif "x_range" in kwargs:
                plot = _is_data_in_range(df, x[i], y[i], kwargs["x_range"])
            elif "y_range" in kwargs:
                plot = _is_data_in_range(df, x[i], y[i], y_range=kwargs["y_range"])

            if len(df[x[i]]) == 0 or len(df[y[i]]) == 0:
                plot = False

            if plot:
                aggs.append(cvs.line(df, x[i], y[i]))
                if colors:
                    cs.append(colors[i])

    if not aggs:
        return xr.DataArray(np.zeros((kwargs["plot_width"], kwargs["plot_height"])))

    if colors:
        imgs = [tf.shade(aggs[i], cmap=[c]) for i, c in enumerate(cs)]
        return tf.stack(*imgs)
    else:
        imgs = [tf.shade(aggs[i]) for i, c in range(len(y))]
        return tf.stack(*imgs)


def get_ranges(data, x, y):
    """"""
    if isinstance(y, (list, tuple)) and isinstance(x, str):
        x = [x] * len(y)

    if isinstance(y, str):
        if isinstance(x, list):
            raise ValueError("If y is an str, then x should also be a str.")
        else:
            x = [x]
        y = [y]

    if len(x) != len(y):
        raise ValueError("x and y should be the same length.")

    finfo = np.finfo(float)
    x_range = (finfo.max, finfo.min)
    y_range = (finfo.max, finfo.min)
    if isinstance(data, (dict, pd.DataFrame)):
        xs = np.array([[min(data[x_col]), max(data[x_col])] for x_col in x if len(data[x_col])])
        ys = np.array([[min(data[y_col]), max(data[y_col])] for y_col in y if len(data[y_col])])
        if len(xs) and len(ys):
            x_range = (np.min(xs[:, 0]), np.max(xs[:, 1]))
            y_range = (np.min(ys[:, 0]), np.max(ys[:, 1]))
    elif isinstance(data, (list, tuple)):
        if len(y) != len(data):
            raise ValueError(
                "When data is supplied as a list or tuple "
                "then y and data should be the same length."
            )
        for i, line in enumerate(data):
            if not len(line[x[i]]) or not len(line[y[i]]):
                continue
            x_range = (min(min(line[x[i]]), x_range[0]), max(max(line[x[i]]), x_range[1]))
            y_range = (min(min(line[y[i]]), y_range[0]), max(max(line[y[i]]), y_range[1]))

    if x_range[0] == y_range[0] == finfo.max or x_range[1] == y_range[0] == finfo.min:
        return (0.0, 1.0), (0.0, 1.0)
    return x_range, y_range


class ShadedTimeSeries(BasePlot):
    """"""

    def __init__(
        self, doc, data, x, y, colors=None, refresh_rate=1000, **kwargs,
    ):
        """"""
        super().__init__(doc, refresh_rate)

        self._kwargs = kwargs
        self._fixe_range = False
        self.throttledEvent = ThrottledEvent(doc, 50)

        self._x = x
        self._y = y
        self._colors = colors
        self._data = data

        self._x_range, self._y_range = get_ranges(data, x, y)
        self._current_x_range, self._current_y_range = self._x_range, self._y_range
        self._plot_width = 800
        self._plot_height = 300

        defaults_opts = dict(plot_width=800, plot_height=300, title="")

        defaults_opts.update(
            (key, value) for key, value in kwargs.items() if key in get_figure_options()
        )

        if "x_range" in kwargs:
            self._current_x_range = kwargs["x_range"]
        if "y_range" in kwargs:
            self._current_y_range = kwargs["y_range"]

        img = shade(
            data,
            x,
            y,
            colors,
            plot_width=kwargs["plot_width"],
            plot_height=kwargs["plot_height"],
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

        self._root = figure(**kwargs)
        self._root.x_range.range_padding = self._root.y_range.range_padding = 0
        self._root.image_rgba(image="img", source=self._ds, x="x", y="y", dw="dw", dh="dh")
        self._root.on_event(Reset, self._reset)

    def _reshade(self):
        """"""

        def gen():
            img = shade(
                self._data,
                self._x,
                self._y,
                self._colors,
                plot_width=self._plot_width,
                plot_height=self._plot_height,
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

        self.throttledEvent.add_event(gen)

    def _reset(self, event):
        """"""
        self._x_range, self._y_range = get_ranges(self._data, self._x, self._y)
        self._current_x_range, self._current_y_range = self._x_range, self._y_range
        self._reshade()

    def update(self):
        """"""
        x_range = (float(self._root.x_range.start), float(self._root.x_range.end))
        y_range = (float(self._root.y_range.start), float(self._root.y_range.end))

        x_start = float(self._ds.data["x"][0])
        x_end = float(x_start + self._ds.data["dw"][0])
        y_start = float(self._ds.data["y"][0])
        y_end = float(y_start + self._ds.data["dh"][0])

        if (
            x_range[0] != x_start
            or x_range[1] != x_end
            or y_range[0] != y_start
            or y_range[1] != y_end
        ):
            self._current_x_range = x_range
            self._current_y_range = y_range
            self._reshade()

    def set_data(self, data, x, y, colors=None, x_range=None, y_range=None):
        """"""
        self._data = data
        self._x = x
        self._y = y

        _x_range, _y_range = get_ranges(data, x, y)
        if not x_range:
            x_range = _x_range
        if not y_range:
            y_range = _y_range
        if colors:
            self._colors = colors

        self._current_x_range = x_range
        self._current_y_range = y_range

        self._reshade()

    def set_range(self, x_range=None, y_range=None):
        if x_range:
            self._current_x_range = y_range
        if y_range:
            self._current_y_range = y_range
        self._reshade()
