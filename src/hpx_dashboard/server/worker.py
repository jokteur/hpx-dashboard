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
import heapq
import threading
import itertools
import traceback
import time

from ..common.singleton import Singleton
from ..common.logger import Logger


class WorkerQueue(metaclass=Singleton):
    """"""

    def __init__(self):
        self._queue = []
        self._entry_finder = {}
        self._removed = "<removed>"
        self._counter = itertools.count()
        self._lock = threading.Lock()

    def put(self, task_name, task, priority=0):
        "Add a new task or update the priority of an existing task"
        with self._lock:
            if task_name in self._entry_finder:
                entry = self._entry_finder.pop(task_name)
                entry[-1] = self._removed
            count = next(self._counter)
            entry = [priority, count, task, task_name]
            self._entry_finder[task_name] = entry
            heapq.heappush(self._queue, entry)

    def get(self):
        with self._lock:
            while self._queue:
                _, _, task, task_name = heapq.heappop(self._queue)
                if task_name is not self._removed:
                    del self._entry_finder[task_name]
                    return task

            return lambda: time.sleep(1e-3)


def worker_thread(queue: WorkerQueue):
    """"""
    while True:
        try:
            task = queue.get()
            task()
        except Exception as e:
            Logger().error(e)
            traceback.print_exc()
