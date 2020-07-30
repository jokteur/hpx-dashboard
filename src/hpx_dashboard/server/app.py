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

from .plots import TasksPlot


def app(doc):
    # threads_count = Threads2(doc)
    plot = TasksPlot(doc, "Task plot")

    # put the button and plot in a layout and add to the document
    p = plot.plot()
    doc.add_root(column(p))
    return p
