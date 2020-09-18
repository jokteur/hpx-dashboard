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

import os

from bokeh.layouts import row
from bokeh.models import Panel, Tabs
from bokeh.themes import Theme

from jinja2 import Environment, FileSystemLoader

from .utils import Notifier
from .data import format_instance
from .plots import TasksPlot, TimeSeries
from .widgets import DataCollectionWidget, CustomCounterWidget, empty_placeholder

env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "http", "templates"))
)
BOKEH_THEME = Theme(os.path.join(os.path.dirname(__file__), "http", "bokeh_theme.yaml"))


def custom_counters(doc, notifier):
    """Defines the tab for the custom counter widget"""
    custom_counter = CustomCounterWidget(doc)
    return custom_counter.layout()


def scheduler(doc, notifier):
    """Defines the tab for the task plot"""

    # TODO : if there are multiple pools, plot all the lines

    scheduler_plot = TimeSeries(
        doc, shade=True, title="Scheduler utilization", y_axis_label="Utilization (%)"
    )
    counter = "threads/count/instantaneous/pending"
    instance = format_instance("0")
    pretty_name = "Scheduler utilization"
    scheduler_plot.add_line(
        counter,
        instance,
        pretty_name=pretty_name,
    )

    def _reset_lines(collection):
        nonlocal scheduler_plot

        scheduler_plot.remove_all()
        scheduler_plot.add_line(counter, instance, collection, pretty_name=pretty_name)

    notifier.subscribe(_reset_lines)
    return scheduler_plot.layout()


def tasks(doc, notifier):
    """Defines the tab for the task plot"""
    task_plot = TasksPlot(doc)
    notifier.subscribe(task_plot.set_collection)
    return task_plot.layout()
    return empty_placeholder()


def standalone_doc(extra, doc):
    doc.title = "HPX performance counter dashboard"
    notifier = Notifier()

    widget = DataCollectionWidget(doc, notifier.notify)

    task_tab = Panel(child=tasks(doc, notifier), title="Tasks plot")
    scheduler_tab = Panel(child=scheduler(doc, notifier), title="Scheduler utilization")
    custom_counter_tab = Panel(child=custom_counters(doc, notifier), title="Customizable plots")

    doc.add_root(
        row(
            Tabs(tabs=[scheduler_tab, task_tab, custom_counter_tab]),
            widget.layout(),
            sizing_mode="scale_width",
        )
    )

    doc.template = env.get_template("normal.html")
    doc.template_variables.update(extra)
    doc.theme = BOKEH_THEME
