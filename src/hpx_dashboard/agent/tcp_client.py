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

import asyncio
import time

from ..common.constants import message_separator
from ..common.logger import Logger


async def connect(host: str, port: int, timeout=2):
    """"""
    writer = None
    prev_time = time.time()
    while True:
        try:
            _, writer = await asyncio.open_connection(host, port)
        except (asyncio.TimeoutError, ConnectionRefusedError):
            pass

        if time.time() - prev_time > timeout:
            break

        if writer:
            break
        time.sleep(0.01)

    return writer


async def send_data(host, port, timeout, queue, stop_signal):
    """"""
    writer = await connect(host, port, timeout)
    logger = Logger()

    if not writer:
        logger.error(
            f"Timeout error: could not connect to {host}:{port}" f" after {timeout} seconds"
        )
        stop_signal.stop = True
        return

    while True:  # not stop_signal.stop:
        line = queue.get()

        if line is None:
            break

        writer.write(line + message_separator)
        await writer.drain()
        queue.task_done()

    return
