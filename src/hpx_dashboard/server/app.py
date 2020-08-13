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

from .data import format_instance
from .plots import TimeSeries


def app(doc):
    # threads_count = Threads2(doc)
    plot = TimeSeries(doc, title="Active threads", shade=True)

    plot.add_line(
        "threads/count/instantaneous/staged", format_instance("0"), pretty_name="Active threads"
    )
    plot.add_line(
        "threads/count/instantaneous/pending", format_instance("0"), pretty_name="Active threads #1"
    )

    # # put the button and plot in a layout and add to the document
    p = plot.plot()

    doc.add_root(column(p))
    return p
