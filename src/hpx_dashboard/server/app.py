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

# from .data import format_instance
from .plots import Dummy
from .plots.raster import ShadedTimeSeries


def app(doc):
    data = {"x": [], "y": []}
    a = ShadedTimeSeries(doc, data, "x", "y")
    data = {"x": list(range(1000)), "y": list(range(1000))}
    a.set_data(data, "x", "y")

    # threads_count = Threads2(doc)
    # plot = TimeSeries(doc, title="Active threads", shade=True)

    # for i in range(0, 32):
    #     plot.add_line(
    #         "threads/count/instantaneous/staged",
    #         format_instance("0", thread_id=i, is_total=False),
    #         pretty_name=f"Thread {i}",
    #     )
    #     plot.add_line(
    #         "threads/count/instantaneous/pending",
    #         format_instance("0", thread_id=i, is_total=False),
    #         pretty_name=f"Thread {i}",
    #     )

    plot = Dummy(doc)
    # plot.add_line(
    #     "threads/count/instantaneous/staged",
    #     format_instance("0", thread_id=0, is_total=False),
    #     pretty_name=f"Thread {0}",
    # )
    # put the button and plot in a layout and add to the document
    p = plot.plot()

    doc.add_root(column(p))
    return p
