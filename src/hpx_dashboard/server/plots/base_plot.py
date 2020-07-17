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

from abc import ABCMeta


class BasePlot(metaclass=ABCMeta):
    """"""

    def __init__(self, doc, title, refresh_rate=100):
        """"""
        self.plot = None
        self.title = title
        self.buffer = None
        self.doc = doc
        doc.add_periodic_callback(self.update, refresh_rate)

    def stop_update(self):
        self.doc.remove_periodic_callback(self.update)

    def update(self):
        pass

    def get_plot(self):
        return self.plot
