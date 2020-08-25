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
import functools

from bokeh.server.server import Server

from .components import standalone_doc
from .http.statics import routes

applications = {
    "/": standalone_doc,
}

template_variables = {}


def bk_server(prefix="/", **kwargs):
    apps = {k: functools.partial(v, template_variables) for k, v in applications.items()}
    return Server(apps, extra_patterns=[] + routes, **kwargs)
