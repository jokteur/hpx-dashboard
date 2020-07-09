"""
"""

__copyright__ = "Copyright (C) 2020 ETHZ"
__licence__ = "BSD 3"

import asyncio
import time

class TimeOutError(Exception):
    """Exception class for timeouts"""
    pass

async def connect(host: str, port: int, timeout=2):
    """"""
    writer = None
    prev_time = time.time()
    while True:
        try:
            _, writer = await asyncio.open_connection(host, port)
        except:
            pass
        finally:
            break

        if time.time() - prev_time > timeout:
            break
        time.sleep(0.01)

    if not writer:
        raise TimeOutError

    return writer

async def send_data(writer, queue):
    """"""
    while True:
        line = await queue.get()
        writer.write(line + b'\r\n')
        queue.task_done()