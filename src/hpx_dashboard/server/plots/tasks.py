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
from bokeh.layouts import column
from bokeh.models import MultiChoice  # , HoverTool

from .base import BaseElement, get_figure_options
from ..data import DataSources
from .raster import ShadedTaskPlot, empty_task_mesh
from ..widgets import BaseWidget

# from ..utils import format_time


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

        self._last_run = -1

        self._task_names = set()
        self._filter_list = []
        self._locality = "0"

        # Make plot and figure
        defaults_opts = dict(
            title="Task plot",
            tools="save,reset,xwheel_zoom,xpan",
            toolbar_location="above",
            x_axis_label="Time (s)",
            y_axis_label="Worker ID",
            plot_width=800,
            plot_height=600,
        )

        defaults_opts.update(
            (key, value) for key, value in kwargs.items() if key in get_figure_options()
        )

        self._num_points = 0

        self._figure = ShadedTaskPlot(
            doc,
            *empty_task_mesh,
            [],
            [],
            refresh_rate=refresh_rate,
            **defaults_opts,
        )

        self._filter_choice = FilterWidget(doc, self.set_filter_list, collection=collection)

        # Right now, filtering is not implemented
        self._root = column(self._figure.layout())  # , self._filter_choice.layout())

    def set_filter_list(self, filters):
        """Sets a filter to show only particular tasks"""
        if isinstance(filters, str):
            self._filter_list = [filters]
        elif isinstance(filters, list):
            self._filter_list = filters

        self._num_points = -1

    def _update_data(self):
        """"""
        collection = DataSources().get_collection(self._collection)
        if not collection:
            return

        names = collection.get_task_names(self._locality)
        if names != self._task_names:
            self._task_names = names
            self._filter_choice.set_choices(names)

        verts, tris, data_ranges = collection.get_task_mesh_data(self._locality)
        task_data, names = collection.get_task_data(self._locality)
        if len(verts) != self._num_points:
            self._figure.set_data(verts, tris, data_ranges, names, task_data)
            self._num_points = len(verts)

    def set_instance(self, locality):
        self._locality = locality
        self._num_points = -1
        self._update_data()

    def update(self):
        super().update()
        self._update_data()
