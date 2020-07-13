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
import traceback

from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError

from .data_aggregator import DataAggregator
from ..common.constants import message_separator
from ..common.logger import Logger


class Server(TCPServer):
    """
    overrides handle_stream"""

    async def handle_stream(self, stream, address) -> None:
        """Handle the stream of incoming data over TCP

        Parameters
        ----------
        stream
            TCP stream
        address
            address to read from
        """
        data_aggregator = DataAggregator()
        logger = Logger()

        while True:
            try:
                response = await stream.read_until(message_separator)
                response_type, data = pickle.loads(response)

                if response_type == "counter-data" and data_aggregator.current_run is not None:
                    data_aggregator.current_collection().add_line(*data)
                elif response_type == "line":
                    print(data)
                elif response_type == "transmission_begin":
                    print("BEGIN")
                    data_aggregator.new_collection(data)
                elif response_type == "transmission_end":
                    data_aggregator.finalize_current_collection(data)
                    print("END")
                elif response_type == "counter-infos" and data_aggregator.current_run is not None:
                    data_aggregator.set_counter_infos(data)
            except StreamClosedError:
                stream.close(exc_info=True)
                return
            except Exception as e:
                logger.error(e)
                traceback.print_exc()
