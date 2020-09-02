# -*- coding: utf-8 -*-
#
# HPX - dashboard
#
# Copyright (c) 2020 - ETH Zurich
# All rights reserved
#
# SPDX-License-Identifier: BSD-3-Clause

"""
"""
from collections import OrderedDict

from bokeh.plotting import Figure
from bokeh.layouts import column
from bokeh.models import Legend, LegendItem

from ..data import DataSources
from ..widgets import empty_placeholder
from .base import BaseElement, get_colors, get_figure_options
from .raster import ShadedTimeSeries


class TimeSeries(BaseElement):
    """"""

    def __init__(self, doc, shade=False, refresh_rate=500, **kwargs):
        """"""
        super().__init__(doc, refresh_rate=refresh_rate)

        self._defaults_opts = dict(
            plot_width=800, plot_height=400, title="", x_axis_label="Time (s)"
        )
        self._defaults_opts.update(
            (key, value) for key, value in kwargs.items() if key in get_figure_options()
        )

        self._data_sources = OrderedDict()
        self._names = OrderedDict()
        self._glyphs = OrderedDict()

        # For shaded data
        self._data = []
        self._x = []
        self._y = []
        self._colors = []
        self._color_ids = OrderedDict()

        self._rebuild_figure = True

        self._figure = None
        self._reshade = True
        self._x_range = None
        self._y_range = None

        self._is_shaded = shade
        self._root = column(empty_placeholder())
        self._show_legend = False

    def add_line(self, countername, instance, collection=None, pretty_name=None):
        """"""
        key = (countername, instance, collection, pretty_name)

        if not pretty_name:
            pretty_name = f"{countername};{instance};{collection}"

        ds = DataSources().get_data(self._doc, countername, instance, collection)
        self._data_sources[key] = ds
        names = [name for _, _, _, name in self._data_sources.keys()]
        self._colors = get_colors("Category20", names)

        DataSources().listen_to(self._set_update, self._doc, countername, instance, collection)

        if self._is_shaded:
            self._reshade = True
        else:
            self._make_figure()
            self._rebuild_figure = False

        print(ds["data_source"].data[ds["x_name"]])

    def remove_line(self, countername, instance, collection=None, pretty_name=None):
        """"""
        # TODO: does not update the plot correctly right now
        key = (countername, instance, collection, pretty_name)
        if key in self._data_sources:
            del self._data_sources[key]
            del self._glyphs[key]
        self._make_figure()

    def remove_all(self):
        """"""
        self._data_sources.clear()
        self._glyphs.clear()
        self._make_figure()

    def update(self):
        if self._reshade and self._is_shaded:
            self._data = []
            self._x = []
            self._y = []
            for key, ds in self._data_sources.items():
                self._data.append(ds["data_source"].data)
                self._x.append(ds["x_name"])
                self._y.append(ds["y_name"])

        # Rebuild the figure in case the user switched from shaded or vice-versa
        if self._rebuild_figure:
            self._make_figure()
            self._rebuild_figure = False
            self._reshade = False

        if self._reshade and self._is_shaded:
            self._shaded_fig.set_data(
                self._data, self._x, self._y, self._colors, self._x_range, self._y_range,
            )
            self._reshade = False

    def _build_legend(self):
        legend_items = []
        for i, key in enumerate(self._glyphs.keys()):
            _, _, _, name = key
            legend_items.append(LegendItem(label=name, renderers=[self._glyphs[key]], index=i))

        self._figure.add_layout(
            Legend(items=legend_items, location="top_left", orientation="horizontal"), "above"
        )

    def _set_update(self):
        self._reshade = True

    def _make_figure(self):
        if self._figure:
            del self._figure
            self._glyphs.clear()

        if self._is_shaded:
            self._shaded_fig = ShadedTimeSeries(
                self._doc, self._data, self._x, self._y, self._colors, **self._defaults_opts,
            )
            self._figure = self._shaded_fig.plot()
        else:
            self._figure = Figure(**self._defaults_opts)

            for key, ds in self._data_sources.items():
                if key not in self._glyphs:
                    index = list(self._data_sources.keys()).index(key)
                    self._glyphs[key] = self._figure.line(
                        x=ds["x_name"],
                        y=ds["y_name"],
                        source=ds["data_source"],
                        line_color=self._colors[index],
                        line_width=2,
                    )

        self._build_legend()
        self._root.children[0] = self._figure
