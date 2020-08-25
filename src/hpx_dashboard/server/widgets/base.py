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

from bokeh.models.widgets import Div

from ..plots import BaseElement


def empty_placeholder():
    return Div(text=" ")


class BaseWidget(BaseElement):
    """"""

    def __init__(self, doc, callback=None, refresh_rate=500, collection=None, **kwargs):
        """"""
        super().__init__(doc, refresh_rate, collection)

        self._callback = callback
