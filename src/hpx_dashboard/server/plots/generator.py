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

from bokeh.plotting import figure
from bokeh.models import RangeTool
from bokeh.models.ranges import Range1d
from bokeh.layouts import column
from bokeh.models.widgets import Div

from ..data import DataSources, format_instance, DataAggregator
from .base_plot import BasePlot, default_colors


class PlotGenerator(BasePlot):
    """"""

    def __init__(self, doc, title, refresh_rate=100, **kwargs):
        """"""
        super().__init__(doc, title, refresh_rate)
        self.plot = figure(title=title, **kwargs)

        self.plot_number = 0

    def add_plot(self, collection, counter_name, instance):
        """"""
        data = DataSources().get_data(counter_name, instance, collection=collection)

        self.plot.line(
            x=data["x_name"],
            y=data["y_name"],
            source=data["data_source"],
            color=default_colors[self.plot_number % len(default_colors)],
        )
        self.plot_number += 1


class TimeSeries(BasePlot):
    """"""

    def __init__(
        self,
        doc,
        countername,
        title,
        locality_id="0",
        x_range=(0, 10),
        plot_all_workers=True,
        refresh_rate=500,
        **kwargs,
    ):
        """"""
        super().__init__(doc, title, refresh_rate)

        self._title = title
        self._countername = countername
        self._collection = None
        self._kwargs = kwargs
        self._locality_id = locality_id
        self._plot_all_workers = plot_all_workers
        self._num_plots = 0
        self._x_range = Range1d(*x_range, bounds=(0, None))

        self._figures = []
        self._data_sources = []
        self.layout = column(Div(text=" "))

        self._set_data()
        self._make_plots("0")
        self.start_update()

    def _set_data(self, collection=None):
        """"""
        previous_collection = self._collection
        if collection:
            self._collection = collection
        else:
            current_collection = DataAggregator().get_current_run()
            if current_collection:
                self._collection = current_collection
            else:
                self._collection = DataAggregator().get_last_run()

        if self._collection or self._collection != previous_collection:
            num_plots = self._collection.get_num_worker_threads(self._locality_id)
            if num_plots != self._num_plots:
                self._make_plots("0")
                self._num_plots = num_plots

    def update(self):
        """"""
        self._set_data()
        last_time = self._data_sources[0]["last_time"]
        if last_time > 0 and self._x_range.bounds != last_time:
            self._x_range.bounds = (0, last_time)

    def _make_plots(self, instance):
        """"""
        instances = []
        if self._collection:
            if self._plot_all_workers:
                for pool in self._collection.get_pools(self._locality_id):
                    for worker in self._collection.get_worker_threads(self._locality_id, pool):
                        instances.append(
                            (
                                f"pool #{pool}; worker #{worker}",
                                format_instance(self._locality_id, pool, worker, False),
                            )
                        )
            else:
                instances.append(("total", format_instance(self._locality_id)))
        else:
            instances.append(("total", format_instance(self._locality_id)))

        _figure = figure(
            plot_height=300,
            tools="xpan",
            x_range=self._x_range,
            toolbar_location=None,
            x_axis_label="Time (s)",
            **self._kwargs,
        )
        self._figures = []
        for i, (name, instance) in enumerate(instances):
            data = DataSources().get_data(
                self.doc, self._countername, instance, collection=self._collection
            )
            self._data_sources.append(data)
            _figure.line(
                x=data["x_name"],
                y=data["y_name"],
                source=data["data_source"],
                color=default_colors[i % 6],
                legend_label=name,
            )

        self._select = figure(
            title="Drag the middle and edges of the selection box to change the range above",
            plot_height=130,
            tools="",
            toolbar_location=None,
            x_axis_label="Time (s)",
            x_axis_location="above",
            y_axis_type=None,
            y_axis_label="Total",
            background_fill_color="#efefef",
            **self._kwargs,
        )

        range_tool = RangeTool(x_range=self._x_range)
        range_tool.overlay.fill_color = "navy"
        range_tool.overlay.fill_alpha = 0.2

        select_ds = DataSources().get_data(
            self.doc, self._countername, format_instance(0), collection=self._collection
        )
        self._select.line(
            x=select_ds["x_name"],
            y=select_ds["y_name"],
            source=select_ds["data_source"],
            color="black",
        )
        self._select.ygrid.grid_line_color = None
        self._select.add_tools(range_tool)
        self._select.toolbar.active_multi = range_tool

        self.layout.children[0] = column(self._select, _figure)
