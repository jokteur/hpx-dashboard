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
from queue import Queue
import traceback

from ..common.singleton import Singleton
from ..common.logger import Logger


class WorkerQueue(metaclass=Singleton):
    """This class is just for accessing the Worker queue from different threads."""

    def __init__(self):
        self._queue = Queue()

    def get(self):
        return self._queue


def worker_thread(queue: WorkerQueue):
    """"""
    queue = queue.get()
    while True:
        try:
            task = queue.get()
            task()
        except Exception as e:
            Logger().error(e)
            traceback.print_exc()
