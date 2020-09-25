import time
from functools import partial
import colorcet

from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
from bokeh.events import Reset, MouseWheel, PanEnd, MouseMove
import numpy as np
import pandas as pd
import xarray as xr
import datashader as ds
import datashader.transfer_functions as tf

from .base import BaseElement, ThrottledEvent, get_figure_options
from ..utils import format_time
from ..worker import WorkerQueue
from ...common.constants import task_cmap

empty_task_mesh = [
    [[0, 0, 0, 0]],
    [[0, 0, 0]],
    ((0, 1), (0, 1)),
]


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
    """Returns true if the both range are close enough (within a relative epsilon)."""
    if not range1[0] or not range2[0]:
        return False
    return abs(range1[0] - range2[0]) < epsilon and abs(range1[1] - range2[1]) < epsilon


def shade_mesh(vertices, triangles, cmap=colorcet.rainbow, **kwargs):
    """"""

    if "plot_width" not in kwargs or "plot_height" not in kwargs:
        raise ValueError("Please provide plot_width and plot_height for the canvas.")

    if not isinstance(vertices, pd.DataFrame):
        vertices = pd.DataFrame(vertices, columns=["x", "y", "z", "patch_id"], copy=False)

    if not isinstance(triangles, pd.DataFrame):
        triangles = pd.DataFrame(triangles, columns=["v0", "v1", "v2"], copy=False)

    cvs = ds.Canvas(**kwargs)
    img = cvs.trimesh(vertices, triangles, interpolate="nearest")

    summary = ds.summary(id_info=ds.max("patch_id"))
    summary.column = "z"

    hover_agg = cvs.trimesh(vertices, triangles, agg=summary)
    res = tf.shade(img, cmap=cmap, how="linear", span=[0, len(cmap)]), hover_agg

    return res


def shade_line(data, colors=None, **kwargs):
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


def _is_equal(x, y, epsilon=1e-6):
    return abs(x - y) < epsilon


class ShadedPlot(BaseElement):
    """"""

    def __init__(
        self,
        doc,
        refresh_rate=500,
        **kwargs,
    ):
        """"""
        super().__init__(doc, refresh_rate)

        self._kwargs = kwargs
        self._throttledEvent = ThrottledEvent(doc, 50)

        # Variable for freezing the ranges if the user interacted with the plot
        self._keep_range = False

        self._current_x_range, self._current_y_range = self._calculate_ranges()
        self._bokeh_x_range, self._bokeh_y_range = self._current_x_range, self._current_y_range
        self._num_range_updates = 0

        self._defaults_opts = dict(plot_width=800, plot_height=300, title="")

        self._defaults_opts.update(
            (key, value) for key, value in kwargs.items() if key in get_figure_options()
        )

        if "x_range" in self._defaults_opts:
            self._current_x_range = self._defaults_opts["x_range"]
        if "y_range" in self._defaults_opts:
            self._current_y_range = self._defaults_opts["y_range"]

        self._root = figure(**self._defaults_opts)

        self._root.on_event(MouseWheel, self._freeze_ranges)
        self._root.on_event(PanEnd, self._freeze_ranges)

        self._root.x_range.range_padding = self._root.y_range.range_padding = 0
        self._root.on_event(Reset, self._reset_fct)

    def _reset_fct(self, event):
        """"""
        self._current_x_range, self._current_y_range = self._calculate_ranges()
        self._reshade()
        self._keep_range = False
        self._last_reset = time.time()

    def _freeze_ranges(self, *args):
        self._keep_range = True

    def _calculate_ranges(self):
        return (0, 1), (0, 1)

    def _reshade(self, immediate=False):
        pass

    def set_data(self):
        pass

    def update(self):
        if self._keep_range:
            x_range = self._root.x_range
            y_range = self._root.y_range
            x_range = (x_range.start, x_range.end)
            y_range = (y_range.start, y_range.end)

            if x_range == self._bokeh_x_range and x_range == self._bokeh_x_range:
                self._num_range_updates += 1
            else:
                self._num_range_updates = 0
            self._bokeh_x_range = x_range
            self._bokeh_y_range = y_range
            if self._num_range_updates > 2:
                return

            if x_range[0]:
                self._current_x_range = x_range
            if y_range[0]:
                self._current_y_range = y_range
            self._reshade(True)

    def set_range(self, x_range=None, y_range=None):
        if x_range:
            self._current_x_range = y_range
        if y_range:
            self._current_y_range = y_range
        self._reshade()


class ShadedTaskPlot(ShadedPlot):
    """"""

    def __init__(
        self,
        doc,
        vertices,
        triangles,
        data_ranges,
        names,
        data,
        refresh_rate=500,
        **kwargs,
    ):
        self._vertices = vertices
        self._triangles = triangles
        self._data_ranges = data_ranges
        self._names = names
        self._data = data
        self._hovered_mesh = empty_task_mesh[0:2]  # For highlighting the hovered task on the plot
        self._last_hovered = -1

        self._throttled_mouseEvent = ThrottledEvent(doc)

        super().__init__(doc, refresh_rate, **kwargs)

        self._img, self._hover_agg = shade_mesh(
            vertices,
            triangles,
            task_cmap,
            plot_width=self._defaults_opts["plot_width"],
            plot_height=self._defaults_opts["plot_height"],
            x_range=self._current_x_range,
            y_range=self._current_y_range,
        )
        self._ds = ColumnDataSource(
            {
                "img": [self._img.values],
                "dw": [self._current_x_range[1] - self._current_x_range[0]],
                "dh": [self._current_y_range[1] - self._current_y_range[0]],
                "x": [self._current_x_range[0]],
                "y": [self._current_y_range[0]],
            }
        )

        # When the user hovers with the mouse on a task, it becomes highlighted
        self._hovered_img, _ = shade_mesh(
            *self._hovered_mesh,
            "black",
            plot_width=self._defaults_opts["plot_width"],
            plot_height=self._defaults_opts["plot_height"],
            x_range=self._current_x_range,
            y_range=self._current_y_range,
        )
        self._hovered_ds = ColumnDataSource(
            {
                "img": [self._hovered_img.values],
                "dw": [self._current_x_range[1] - self._current_x_range[0]],
                "dh": [self._current_y_range[1] - self._current_y_range[0]],
                "x": [self._current_x_range[0]],
                "y": [self._current_y_range[0]],
            }
        )

        self._hover_tool = HoverTool()
        self._root.on_event(MouseMove, self._mouse_move_event)
        self._root.add_tools(self._hover_tool)
        self._root.image_rgba(image="img", source=self._ds, x="x", y="y", dw="dw", dh="dh")
        self._root.image_rgba(image="img", source=self._hovered_ds, x="x", y="y", dw="dw", dh="dh")

    def _calculate_ranges(self):
        return self._data_ranges

    def _mouse_move_event(self, event):
        def update():
            nonlocal event

            # Convert plot coordinate to image coordinate
            x = (
                int(
                    self._defaults_opts["plot_width"]
                    * (event.x - self._current_x_range[0])
                    / (self._current_x_range[1] - self._current_x_range[0])
                )
                - 1
            )
            y = (
                int(
                    self._defaults_opts["plot_height"]
                    * (event.y - self._current_y_range[0])
                    / (self._current_y_range[1] - self._current_y_range[0])
                )
                - 1
            )

            shape = self._hover_agg["id_info"].values.shape
            tooltip = False
            id_patch = -1
            if x < shape[1] and y < shape[0]:
                id_patch = self._hover_agg["id_info"].values[y, x]
                if not np.isnan(id_patch):
                    id_patch = int(id_patch)
                    begin = self._data[id_patch, 1]
                    end = self._data[id_patch, 2]
                    digits = abs(int(np.ceil(np.log10(end - begin)))) + 3
                    duration = format_time(end - begin)
                    self._hover_tool.tooltips = f"""Name: <b><em>{self._names[id_patch]}</em></b><br />
                        Duration: {duration}<br />
                        Start: {np.round(begin, digits)}s<br />
                        End : {np.round(end, digits)}s"""

                    # Generate mesh for hovered image
                    self._hovered_mesh[0] = self._vertices[id_patch * 4 : (id_patch + 1) * 4]
                    self._hovered_mesh[1] = [[0, 1, 2], [0, 2, 3]]
                    tooltip = True

            if not tooltip:
                self._hover_tool.tooltips = ""
                self._hovered_mesh = empty_task_mesh[0:2]

            id_patch = str(id_patch)

            if id_patch != self._last_hovered:
                self._reshade(only_hover=True)
                self._last_hovered = id_patch

        self._throttled_mouseEvent.add_event(update)

    def _reshade(self, immediate=False, only_hover=False):
        """"""

        def push_to_datasource(ds, img):
            ds.data = {
                "img": [img.values],
                "x": [self._current_x_range[0]],
                "y": [self._current_y_range[0]],
                "dw": [self._current_x_range[1] - self._current_x_range[0]],
                "dh": [self._current_y_range[1] - self._current_y_range[0]],
            }

        def update():
            nonlocal only_hover
            if not only_hover:
                self._img, self._hover_agg = shade_mesh(
                    self._vertices,
                    self._triangles,
                    task_cmap,
                    plot_width=self._defaults_opts["plot_width"],
                    plot_height=self._defaults_opts["plot_height"],
                    x_range=self._current_x_range,
                    y_range=self._current_y_range,
                )

            if not only_hover:
                self._doc.add_next_tick_callback(partial(push_to_datasource, self._ds, self._img))

            self._hovered_img, _ = shade_mesh(
                *self._hovered_mesh,
                "black",
                plot_width=self._defaults_opts["plot_width"],
                plot_height=self._defaults_opts["plot_height"],
                x_range=self._current_x_range,
                y_range=self._current_y_range,
            )
            self._doc.add_next_tick_callback(
                partial(push_to_datasource, self._hovered_ds, self._hovered_img)
            )

        if immediate:
            WorkerQueue().put("task_raster", update)
        else:
            self._throttledEvent.add_event(lambda: WorkerQueue().put("task_raster", update))

    def set_data(
        self,
        vertices,
        triangles,
        data_ranges,
        names,
        data,
        x_range=None,
        y_range=None,
    ):
        """"""
        self._vertices = vertices
        self._triangles = triangles
        self._data_ranges = data_ranges
        self._names = names
        self._data = data

        _x_range, _y_range = self._calculate_ranges()

        if not self._keep_range:
            if x_range:
                self._current_x_range = x_range
            else:
                self._current_x_range = _x_range
            if y_range:
                self._current_y_range = y_range
            else:
                self._current_y_range = _y_range

        self._reshade(True)


class ShadedTimeSeries(ShadedPlot):
    """"""

    def __init__(
        self,
        doc,
        data,
        colors=None,
        refresh_rate=500,
        **kwargs,
    ):
        """"""
        self._colors = colors
        self._data = data

        super().__init__(doc, refresh_rate, **kwargs)

        img = shade_line(
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

        self._root.image_rgba(image="img", source=self._ds, x="x", y="y", dw="dw", dh="dh")

    def _calculate_ranges(self):
        return _normalize_ranges(*get_ranges(self._data))

    def _reshade(self, immediate=False):
        """"""

        def gen():
            img = shade_line(
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

    def set_data(
        self,
        data,
        colors=None,
        x_range=None,
        y_range=None,
    ):
        """"""
        self._data = data

        _x_range, _y_range = self._calculate_ranges()

        if not self._keep_range:
            if x_range:
                self._current_x_range = x_range
            else:
                self._current_x_range = _x_range
            if y_range:
                self._current_y_range = y_range
            else:
                self._current_y_range = _y_range

        if colors:
            self._colors = colors

        self._reshade(True)
