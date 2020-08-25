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

from copy import deepcopy

import numpy as np
from bokeh.plotting import Figure
from bokeh.models import ColumnDataSource, HoverTool

from .base import BaseElement, get_figure_options, get_colors
from ..utils import format_time


class TasksPlot(BaseElement):
    empty_dict = {"x": [], "y": [], "width": [], "name": [], "color": [], "duration": []}

    def __init__(
        self,
        doc,
        locality="0",
        window_size=10,
        worker="*",
        collection=None,
        refresh_rate=200,
        **kwargs,
    ):
        """"""
        super().__init__(doc, refresh_rate, collection)

        self._locality = locality
        self._window_size = window_size
        self._data = ColumnDataSource(self.empty_dict)

        self._worker_opt = worker
        self._workers = {}
        self._last_run = -1

        tmp_list = []
        if worker == "*" and self._collection:
            tmp_list = self._collection.get_worker_threads(locality, "default")
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
            height=0.6,
            color="color",
            line_color="color",
            line_alpha=0.4,
        )

        figure.grid.grid_line_color = None
        figure.axis.axis_line_color = None
        figure.axis.major_tick_line_color = None
        figure.yaxis.axis_label = "Worker Thread"
        figure.xaxis.axis_label = "Time (s)"

        hovertool = figure.select(HoverTool)
        hovertool.tooltips = "Name: @name, Duration: @duration"
        hovertool.point_policy = "follow_mouse"

        self._root = figure

    def _update_data(self):
        """"""
        if not self._collection:
            return

        data_dict = deepcopy(self.empty_dict)
        update = False

        names_list = []
        for worker, index in self._workers.items():
            data = self._collection.get_task_data(self._locality, worker, index)
            if data.ndim == 2:
                self._workers[worker] += data.shape[0]
                update = True

                starts = data[:, 1]
                names = list(data[:, 0])
                names_list += names
                ends = data[:, 2]

                width = ends - starts
                left = np.min(starts)

                data_dict["width"] += list(width)
                data_dict["name"] += names
                data_dict["duration"] += map(format_time, list(width))
                data_dict["x"] += list(width / 2 + starts - left)
                data_dict["y"] += list(int(worker) * np.ones(len(width)))

        data_dict["color"] = get_colors("RdYlGn", names_list)

        if update:
            self._data.stream(data_dict, 1000)

    def set_instance(self, locality, worker):
        tmp_list = []
        if worker == "*" and self._collection:
            tmp_list = self._collection.get_worker_threads(locality, "default")
        elif isinstance(worker, list):
            tmp_list = [worker]

        self._workers = {}
        self._workers.update((key, 0) for key in tmp_list)

    def update(self):
        super().update()
        # Reset data if the collection changed
        if self._reset:
            for worker in self._workers.keys():
                self._workers[worker] = 0
            self._data.data = deepcopy(self.empty_dict)
            self._reset = False

        # Update the list of workers
        if self._worker_opt == "*" and self._collection:
            tmp_list = self._collection.get_worker_threads(self._locality, "default")
            self._workers.update((key, 0) for key in tmp_list if key not in self._workers)

        self._update_data()
