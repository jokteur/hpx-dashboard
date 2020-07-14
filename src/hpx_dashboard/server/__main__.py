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

from bokeh.server.server import Server
from tornado.ioloop import IOLoop

from ..common.logger import Logger
from .tcp_listener import TCP_Server
from .app import app


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

    server = Server({"/": app}, io_loop=IOLoop().current())
    server.start()

    server.io_loop.add_callback(server.show, "/")

    TCP_Server().listen(5268)

    logger.info("http://localhost:5006")
    server.io_loop.start()
