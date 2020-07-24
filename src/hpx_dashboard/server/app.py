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

from .plots.threads import Memory
from .data import DataSources


def app(doc):
    # threads_count = Threads2(doc)
    memory = Memory(doc)
    DataSources().start_update(doc)

    # put the button and plot in a layout and add to the document
    p = memory.get_plot()
    doc.add_root(column(p))
    return p
