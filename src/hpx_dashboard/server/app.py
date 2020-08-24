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
# from .plots import TimeSeries
from .widgets.widgets import DataCollectionWidget


def app(doc):
    # put the button and plot in a layout and add to the document
    widget = DataCollectionWidget(doc, lambda x: x)
    # p = plot.plot()
    p = widget.widget()

    doc.add_root(column(p))
    return p
