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

from bokeh.layouts import column
from bokeh.themes import Theme

from jinja2 import Environment, FileSystemLoader

from .widgets import DataCollectionWidget

env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "http", "templates"))
)
BOKEH_THEME = Theme(os.path.join(os.path.dirname(__file__), "http", "bokeh_theme.yaml"))


def standalone_doc(extra, doc):
    doc.title = "HPX performance counter dashboard"

    widget = DataCollectionWidget(doc, lambda x: x)
    p = widget.widget()
    doc.add_root(column(p, sizing_mode="scale_width",))

    doc.template = env.get_template("normal.html")
    doc.template_variables.update(extra)
    doc.theme = BOKEH_THEME
