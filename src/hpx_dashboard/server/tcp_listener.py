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

from .data import DataAggregator
from ..common.constants import message_separator
from ..common.logger import Logger


def handle_response(queue):
    while True:
        try:
            response = queue.get()
            response_type, data = pickle.loads(response)

            if response_type == "regular-data":
                for response_type, sub_data in data:
                    if response_type == "counter-data" and DataAggregator().current_run is not None:
                        DataAggregator().current_data.add_line(*sub_data)
                        DataAggregator().dummy_counter += 1
                    elif response_type == "line":
                        Logger().info(sub_data)
                    elif response_type == "task-data":
                        DataAggregator().current_data.add_task_data(*sub_data)

            elif response_type == "transmission_begin":
                Logger().info("BEGIN")
                DataAggregator().new_collection(data)
            elif response_type == "transmission_end":
                DataAggregator().finalize_current_collection(data)
                Logger().info("END")
            elif response_type == "counter-infos" and DataAggregator().current_run is not None:
                DataAggregator().set_counter_infos(data)

        except Exception as e:
            Logger().error(e)
            traceback.print_exc()


class TCP_Server(TCPServer):
    """
    overrides handle_stream"""

    def __init__(self, queue, **args):
        super().__init__(**args)
        self._queue = queue

    async def handle_stream(self, stream, address) -> None:
        """Handle the stream of incoming data over TCP

        Parameters
        ----------
        stream
            TCP stream
        address
            address to read from
        """

        while True:
            try:
                response = await stream.read_until(message_separator)
                self._queue.put(response)

            except StreamClosedError:
                stream.close(exc_info=True)
                return
