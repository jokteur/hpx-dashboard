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
from .plots import TasksPlot
from .widgets import DataCollectionWidget

env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "http", "templates"))
)
BOKEH_THEME = Theme(os.path.join(os.path.dirname(__file__), "http", "bokeh_theme.yaml"))


def threads(doc, notifier):
    """Defines the tab for the task plot"""
    task_plot = TasksPlot(doc)
    notifier.subscribe(task_plot.set_collection)
    return task_plot.plot()


def tasks(doc, notifier):
    """Defines the tab for the task plot"""
    task_plot = TasksPlot(doc)
    notifier.subscribe(task_plot.set_collection)
    return task_plot.layout()


def standalone_doc(extra, doc):
    doc.title = "HPX performance counter dashboard"
    notifier = Notifier()

    widget = DataCollectionWidget(doc, notifier.notify)

    task_plot = tasks(doc, notifier)
    task_tab = Panel(child=task_plot, title="Tasks plot")

    doc.add_root(row(Tabs(tabs=[task_tab]), widget.layout(), sizing_mode="scale_width",))

    doc.template = env.get_template("normal.html")
    doc.template_variables.update(extra)
    doc.theme = BOKEH_THEME
