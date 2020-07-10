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

import pickle

from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError


class Server(TCPServer):
    async def handle_stream(self, stream, address):
        while True:
            try:
                request = await stream.read_until(b"\r\n")
                data_type, data = pickle.loads(request)

                if data_type == "line":
                    print(data)
            except StreamClosedError:
                stream.close(exc_info=True)
                return
