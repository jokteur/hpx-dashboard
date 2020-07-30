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

import numpy as np
from bokeh.plotting import Figure
from bokeh.models import ColumnDataSource, HoverTool

from .base import BasePlot, get_figure_options, get_colors
from ..data import DataAggregator


class TasksPlot(BasePlot):
    empty_dict = {"x": [], "y": [], "width": [], "name": [], "color": []}

    def __init__(
        self,
        doc,
        title,
        locality="0",
        window_size=10,
        worker="*",
        collection=None,
        refresh_rate=200,
        **kwargs,
    ):
        """"""
        super().__init__(doc, title, refresh_rate)

        self._locality = locality
        self._window_size = window_size
        self._data = ColumnDataSource(self.empty_dict)

        self._worker_opt = worker
        self._workers = {}
        self._last_run = -1

        self.collection = collection
        if not collection:
            if DataAggregator().get_current_run():
                self.collection = DataAggregator().get_current_run()
            elif DataAggregator().get_last_run():
                self.collection = DataAggregator().get_last_run()

        tmp_list = []
        if worker == "*" and self.collection:
            tmp_list = self.collection.get_worker_threads(locality, "default")
        elif isinstance(worker, list):
            tmp_list = [worker]

        self._workers.update((key, 0) for key in tmp_list)

        # Make plot and figure
        defaults_opts = dict(
            title="Task plot",
            tools="hover,save,reset,xwheel_zoom,xpan",
            toolbar_location="above",
            plot_width=800,
            plot_height=400,
        )

        defaults_opts.update(
            (key, value) for key, value in kwargs.items() if key in get_figure_options()
        )

        figure = Figure(**defaults_opts)
        figure.rect(
            source=self._data,
            x="x",
            y="y",
            width="width",
            height=1,
            color="color",
            line_color="white",
        )

        figure.grid.grid_line_color = None
        figure.axis.axis_line_color = None
        figure.axis.major_tick_line_color = None
        figure.yaxis.axis_label = "Worker Thread"
        figure.xaxis.axis_label = "Time (s)"

        hovertool = figure.select(HoverTool)
        hovertool.tooltips = "@name"
        hovertool.point_policy = "follow_mouse"

        self.layout = figure
        self.start_update()

    def _update_data(self):
        """"""
        if not self.collection:
            return

        data_dict = self.empty_dict
        update = False

        names_list = []
        for i, (worker, index) in enumerate(self._workers.items()):
            data = self.collection.get_task_data(self._locality, worker, index)
            if data.ndim == 2:
                self._workers[worker] += data.shape[0]
                update = True

                starts = data[:, 1].astype(float)
                name = list(data[:, 0].astype(str))
                names_list += name
                ends = data[:, 2].astype(float)

                width = ends - starts
                left = np.min(starts)

                data_dict["width"] += list(width)
                data_dict["name"] += name
                data_dict["x"] += list(width / 2 + starts - left)
                data_dict["y"] += list(i * np.ones(len(width)))

        data_dict["color"] = get_colors("Viridis", names_list)

        if update:
            self._data.stream(data_dict)

    def update(self):
        # Reset data from newest run
        if self._last_run != DataAggregator().last_run and DataAggregator().current_run:
            self._last_run = DataAggregator().last_run
            self._data.data = self.empty_dict

        if DataAggregator().get_current_run():
            self.collection = DataAggregator().get_current_run()
        elif DataAggregator().get_last_run():
            self.collection = DataAggregator().get_last_run()

        # Update the list of workers
        if self._worker_opt == "*" and self.collection:
            tmp_list = self.collection.get_worker_threads(self._locality, "default")
            self._workers.update((key, 0) for key in tmp_list if key not in self._workers)

        self._update_data()
