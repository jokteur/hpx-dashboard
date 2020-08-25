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

from ..data import DataSources
from ..widgets import empty_placeholder
from .base import BaseElement, get_colors, get_figure_options
from .raster import ShadedTimeSeries


class TimeSeries(BaseElement):
    """"""

    _data_sources = OrderedDict()
    _names = OrderedDict()
    _glyphs = OrderedDict()

    # For shaded data
    _data = []
    _x = []
    _y = []
    _colors = []
    _color_ids = OrderedDict()

    _rebuild_figure = True
    _figure = None
    _reshade = True
    _x_range = None
    _y_range = None

    def __init__(self, doc, shade=False, refresh_rate=500, **kwargs):
        """"""
        super().__init__(doc, refresh_rate=refresh_rate)

        self._is_shaded = shade
        self._root = column(empty_placeholder())
        self.start_update()

        self._defaults_opts = dict(plot_width=800, plot_height=400, title="")
        self._defaults_opts.update(
            (key, value) for key, value in kwargs.items() if key in get_figure_options()
        )

    def add_line(self, countername, instance, collection=None, pretty_name=None):
        """"""
        key = (countername, instance, collection)

        if not pretty_name:
            pretty_name = f"{countername};{instance};{collection}"

        ds = DataSources().get_data(self._doc, countername, instance, collection)
        self._data_sources[key] = ds
        self._names[key] = pretty_name
        self._colors = get_colors("Category20", list(self._names.values()))

        DataSources().listen_to(self._set_update, self._doc, countername, instance, collection)

        if self._is_shaded:
            self._reshade = True
        else:
            self._make_figure()
            self._rebuild_figure = False

    def remove_line(self, countername, instance, collection=None):
        """"""
        if (countername, instance, collection) in self._data_sources:
            del self._data_sources[(countername, instance, collection)]
            del self._names[(countername, instance, collection)]
            del self._glyphs[(countername, instance, collection)]

    def remove_all(self):
        """"""
        self._data_sources.clear()
        self._names.clear()
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
                    index = list(self._names.keys()).index(key)
                    self._glyphs[key] = self._figure.line(
                        x=ds["x_name"],
                        y=ds["y_name"],
                        source=ds["data_source"],
                        line_color=self._colors[index],
                    )

        self._root.children[0] = self._figure


# class TimeSeries(BaseElement):
#     """"""

#     _collection = None
#     _num_plots = 0
#     _last_time = 0
#     _update_range = True
#     _toggle = None
#     _data_sources = []

#     def __init__(
#         self,
#         doc,
#         countername,
#         title,
#         locality_id="0",
#         window_size=10,
#         plot_all_workers=True,
#         shade=True,
#         refresh_rate=200,
#         **kwargs,
#     ):
#         """"""
#         super().__init__(doc, title, refresh_rate)

#         self._title = title
#         self._countername = countername
#         self._kwargs = kwargs
#         self._locality_id = locality_id
#         self._plot_all_workers = plot_all_workers
#         self._x_range = Range1d(0, window_size, bounds=(0, None))
#         self._window_size = window_size

#         self._figures = []
#         self._shade = shade
#         self._root = column(Div(text=" "))

#         self._set_data()
#         self._make_plots()
#         self.start_update()

#     def _set_data(self, collection=None):
#         """"""
#         # Set the collection (current, previous, ...)
#         previous_collection = self._collection
#         if collection:
#             self._collection = collection
#         else:
#             current_collection = DataAggregator().get_current_run()
#             if current_collection:
#                 self._collection = current_collection
#             else:
#                 self._collection = DataAggregator().get_last_run()

#         if self._collection or self._collection != previous_collection:
#             num_plots = self._collection.get_num_worker_threads(self._locality_id)
#             if num_plots != self._num_plots:
#                 self._make_plots()
#                 self._num_plots = num_plots

#         # List all the line that we need to plot
#         instances = []
#         if self._collection:
#             if self._plot_all_workers:
#                 for pool in self._collection.get_pools(self._locality_id):
#                     for worker in self._collection.get_worker_threads(self._locality_id, pool):
#                         instances.append(
#                             (
#                                 f"pool #{pool}; worker #{worker}",
#                                 format_instance(self._locality_id, pool, worker, False),
#                             )
#                         )
#             else:
#                 instances.append(("total", format_instance(self._locality_id)))
#         else:
#             instances.append(("total", format_instance(self._locality_id)))

#         # Create the data sources
#         self._data_sources = []
#         for i, (name, instance) in enumerate(instances):
#             data = DataSources().get_data(
#                 self._doc, self._countername, instance, collection=self._collection
#             )
#             self._data_sources.append(data)

#         # The last data source is always the selection DataSource
#         self._data_sources.append(
#             DataSources().get_data(
#                 self._doc,
#                 self._countername,
#                 format_instance(self._locality_id),
#                 collection=self._collection,
#             )
#         )

#         if self._shade:
#             names = [name for name, _ in instances]
#             self._colors = [c for c in get_colors("Viridis", names)]
#             self._data = []
#             self._x = []
#             self._y = []
#             for ds in self._data_sources:
#                 self._x.append(ds["x_name"])
#                 self._y.append(ds["y_name"])
#                 if not ds["data_source"].data[ds["x_name"]]:
#                     self._data.append({ds["x_name"]: [0], ds["y_name"]: [0]})
#                 else:
#                     self._data.append(ds["data_source"].data)

#     def _set_x_range(self, init=False):
#         """"""
#         self._last_time = self._data_sources[0]["last_time"]
#         if self._last_time > 0 and self._x_range.bounds != self._last_time:
#             self._x_range.bounds = (0, self._last_time)

#         if self._update_range or init:
#             self._x_range.start = max(0, self._last_time - self._window_size)
#             self._x_range.end = self._last_time

#     def _build_range_button(self, show=False):
#         """"""
#         if not self._toggle:
#             # Toggle follow for the range_tool
#             self._toggle = Toggle(label="Follow", active=self._update_range, width=100)
#             self._toggle.on_click(self._toggle_follow)

#         if show:
#             if not isinstance(self._root.children[0].children[0], Toggle):
#                 self._root.children[0].children[0] = self._toggle
#         else:
#             if isinstance(self._root.children[0].children[0], Toggle):
#                 self._root.children[0].children[0] = empty_placeholder()

#     def update(self):
#         """"""
#         self._set_data()
#         if DataAggregator().get_current_run():
#             self._set_x_range()
#             self._build_range_button(True)
#         else:
#             self._build_range_button()

#         if self._shade:
#             self._select.set_data(self._data[-1], self._x[-1], self._y[-1])

#     def _toggle_follow(self, event):
#         self._update_range = event

#     def _make_select_plot(self):
#         """"""
#         self._set_data()
#         self._select = ShadedTimeSeries(
#             self._doc,
#             "Drag the middle and edges of the selection box to change the range above",
#             self._data[-1],
#             self._x[-1],
#             self._y[-1],
#             "black",
#             plot_height=130,
#             tools="",
#             toolbar_location=None,
#             x_axis_label="Time (s)",
#             x_axis_location="above",
#             y_axis_type=None,
#             y_axis_label="Total",
#             background_fill_color="#efefef",
#         )

#     def _make_plots(self):
#         """"""
#         self._make_select_plot()
#         print(self._select.plot())
#         self._root.children[0] = column(empty_placeholder(), self._select.plot())
#         # Create the main figure
#         # _figure = figure(
#         #     plot_height=500,
#         #     tools="xpan",
#         #     x_range=self._x_range,
#         #     toolbar_location=None,
#         #     x_axis_label="Time (s)",
#         #     **self._kwargs,
#         # )
#         # names = [name for name, _ in instances]
#         # colors = [c for c in get_colors("Viridis", names)]
#         # data = []
#         # x = []
#         # y = []
#         # for i, (name, instance) in enumerate(instances):
#         #     data = DataSources().get_data(
#         #         self._doc, self._countername, instance, collection=self._collection
#         #     )
#         #     self._data_sources.append(data)
#         #     _figure.line(
#         #         x=data["x_name"],
#         #         y=data["y_name"],
#         #         source=data["data_source"],
#         #         color=colors[i],
#         #         legend_label=name,
#         #     )

#         # # Create the selection figure
#         # self._select = figure(
#         #     title="Drag the middle and edges of the selection box to change the range above",
#         #     plot_height=130,
#         #     tools="",
#         #     toolbar_location=None,
#         #     x_axis_label="Time (s)",
#         #     x_axis_location="above",
#         #     y_axis_type=None,
#         #     y_axis_label="Total",
#         #     background_fill_color="#efefef",
#         #     **self._kwargs,
#         # )

#         # range_tool = RangeTool(x_range=self._x_range)
#         # range_tool.overlay.fill_color = "navy"
#         # range_tool.overlay.fill_alpha = 0.2

#         # select_ds = DataSources().get_data(
#         #     self._doc, self._countername, format_instance(0), collection=self._collection
#         # )
#         # self._select.line(
#         #     x=select_ds["x_name"],
#         #     y=select_ds["y_name"],
#         #     source=select_ds["data_source"],
#         #     color="black",
#         # )
#         # self._select.ygrid.grid_line_color = None
#         # self._select.add_tools(range_tool)
#         # self._select.toolbar.active_multi = range_tool
#         # self._set_x_range(True)

#         # # Layout of the plot
#         # self._root.children[0] = column(empty_placeholder(), self._select, _figure)
