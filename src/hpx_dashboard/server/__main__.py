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
import optparse

from tornado.ioloop import IOLoop

from ..common.logger import Logger
from .tcp_listener import Server


def args_parse(argv):
    """
    Parses the argument list
    """
    parser = optparse.OptionParser()

    parser.add_option(
        "-p",
        "--port-listen",
        dest="port_listen",
        help="port on which the server listens for the incoming parsed data",
        default=5267,
    )

    return parser.parse_args(argv)


if __name__ == "__main__":
    """Main entry for the hpx data server."""
    logger = Logger("hpx-dashboard-server")
    opt, args = args_parse(sys.argv[1:])

    Server().listen(opt.port_listen)
    logger.info("Starting the hpx-dashboard server...")
    IOLoop.instance().start()
