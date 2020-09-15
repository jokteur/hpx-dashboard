# -*- coding: utf-8 -*-
#
# HPX - dashboard
#
# Copyright (c) 2020 - ETH Zurich
# All rights reserved
#
# SPDX-License-Identifier: BSD-3-Clause

from ..common.logger import Logger
from .plots import raster

Logger("hpx-dashboard-server")


# Trigger compilation with datashader
raster.shade({"x": [0], "y": [0]}, plot_width=800, plot_height=400)
