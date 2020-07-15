# -*- coding: utf-8 -*-
#
# HPX - dashboard
#
# Copyright (c) 2020 - ETH Zurich
# All rights reserved
#
# SPDX-License-Identifier: BSD-3-Clause


"""Main entry for the hpx dashboard server
"""

import sys

from .cli import server

if __name__ == "__main__":
    """Main entry for the hpx data server."""
    server(sys.argv)
