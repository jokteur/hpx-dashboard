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

from bokeh.plotting import figure

from ..data import DataSources
from .base_plot import BasePlot, default_colors


class PlotGenerator(BasePlot):
    """"""

    def __init__(self, doc, title, refresh_rate=100, **kwargs):
        """"""
        super().__init__(doc, title, refresh_rate)
        self.plot = figure(title=title, **kwargs)

        self.plot_number = 0

    def add_plot(self, collection, counter_name, instance):
        """"""
        data = DataSources().get_data(counter_name, instance, collection=collection)
        DataSources().start_update(self.doc)

        self.plot.line(
            x=data["x_name"],
            y=data["y_name"],
            source=data["data_source"],
            color=default_colors[self.plot_number % len(default_colors)],
        )
        self.plot_number += 1
