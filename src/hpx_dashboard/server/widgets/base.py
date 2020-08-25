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


def empty_placeholder():
    return Div(text=" ")


class BaseWidget:
    """"""

    instance_num = 0

    def __init__(self, doc, callback, refresh_rate=500, **kwargs):
        """"""
        BaseWidget.instance_num += 1
        self._doc = doc
        self._widget = empty_placeholder()
        self._refresh_rate = refresh_rate
        self._callback = callback
        self._callback_object = doc.add_periodic_callback(self._update_widget, refresh_rate)

    def __del__(self):
        self._doc.remove_periodic_callback(self._callback_object)

    def widget(self):
        return self._widget

    def _update_widget(self):
        pass
