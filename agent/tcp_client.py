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
        time.sleep(0.01)

    return writer


async def send_data(writer, queue):
    """"""
    while True:
        line = await queue.get()
        writer.write(line + b"\r\n")
        queue.task_done()
