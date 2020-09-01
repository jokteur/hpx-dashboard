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
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, HoverTool, MultiChoice

from .base import BaseElement, get_figure_options, get_colors
from ..widgets import BaseWidget
from ..utils import format_time


class FilterWidget(BaseWidget):
    def __init__(self, doc, callback, refresh_rate=500, collection=None, **kwargs):
        super().__init__(
            doc, callback=callback, refresh_rate=refresh_rate, collection=collection, **kwargs
        )

        self._choices = []
        self._root = MultiChoice(options=self._choices, title="Filter tasks")
        self._root.on_change("value", self._on_change)

    def _on_change(self, attr, old, new):
        self._callback(new)

    def set_choices(self, choices):
        if choices != self._choices:
            self._choices = choices
            self._root.options = list(self._choices)


class TasksPlot(BaseElement):
    empty_dict = {"x": [], "y": [], "width": [], "name": [], "color": [], "duration": []}

    def __init__(
        self,
        doc,
        locality="0",
        window_size=10,
        worker="*",
        collection=None,
        refresh_rate=500,
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

        self._task_names = set()
        self._left_time = np.finfo("f").max
        self._filter_list = []

        tmp_list = []
        if worker == "*" and self._collection:
            tmp_list = self._collection.get_worker_threads(locality)
        elif isinstance(worker, list):
            tmp_list = worker
        elif isinstance(worker, str):
            tmp_list = [worker]

        self._workers.update((key, 0) for key in tmp_list)

        # Make plot and figure
        defaults_opts = dict(
            title="Task plot",
            tools="hover,save,reset,xwheel_zoom,xpan",
            toolbar_location="above",
            plot_width=800,
            plot_height=600,
            background_fill_color="black",
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
        hovertool.tooltips = "Worker ID: @y, Name: @name, Duration: @duration"
        hovertool.point_policy = "follow_mouse"

        self._filter_choice = FilterWidget(doc, self.set_filter_list, collection=collection)

        self._root = column(figure, self._filter_choice.layout())

    def set_filter_list(self, filters):
        """Sets a filter to show only particular tasks"""
        if isinstance(filters, str):
            self._filter_list = [filters]
        elif isinstance(filters, list):
            self._filter_list = filters

        self._reset = True

    def get_task_names(self):
        return list(self._task_names)

    def _update_data(self):
        """"""
        if not self._collection:
            return

        data_dict = deepcopy(self.empty_dict)
        update = False

        for worker, index in self._workers.items():
            data = self._collection.get_task_data(self._locality, worker, index)
            if data.ndim == 2:
                self._workers[worker] += data.shape[0]
                update = True

                names = list(data[:, 0])

                self._task_names.update(names)

                starts = data[:, 1]
                ends = data[:, 2]

                width = ends - starts
                start_min = np.min(starts)
                if start_min < self._left_time:
                    self._left_time = start_min

                data_dict["width"] += list(width)
                data_dict["name"] += names
                data_dict["duration"] += map(format_time, width)
                data_dict["x"] += list(width / 2 + starts)
                data_dict["y"] += list(int(worker) * np.ones(len(width)))

        # There is probably a more efficient way of filtering, but this works for now
        # Filtering _has_ to be done after the previous for loop
        if self._filter_list:
            i = len(data_dict["name"]) - 1
            for name in reversed(data_dict["name"]):
                if name not in self._filter_list:
                    del data_dict["width"][i]
                    del data_dict["name"][i]
                    del data_dict["duration"][i]
                    del data_dict["x"][i]
                    del data_dict["y"][i]
                else:
                    data_dict["x"][i] -= self._left_time
                i -= 1
        else:
            for i in range(len(data_dict["x"])):
                data_dict["x"][i] -= self._left_time

        self._filter_choice.set_choices(self._task_names)
        data_dict["color"] = get_colors("Category20", data_dict["name"], False)

        if update:
            self._data.stream(data_dict)

    def set_instance(self, locality, worker):
        tmp_list = []
        if worker == "*" and self._collection:
            tmp_list = self._collection.get_worker_threads(locality)
        elif isinstance(worker, list):
            tmp_list = worker
        elif isinstance(worker, str):
            tmp_list = [worker]

        self._workers = {}
        self._workers.update((key, 0) for key in tmp_list)
        self._update_data()

    def update(self):
        super().update()
        # Reset data if the collection changed
        if self._reset:
            for worker in self._workers.keys():
                self._workers[worker] = 0
            self._data.data = deepcopy(self.empty_dict)
            self._task_names = set()
            self._reset = False
            self._left_time = np.finfo("f").max

        # Update the list of workers
        if self._worker_opt == "*" and self._collection:
            tmp_list = self._collection.get_worker_threads(self._locality)
            self._workers.update((key, 0) for key in tmp_list if key not in self._workers)

        self._update_data()
