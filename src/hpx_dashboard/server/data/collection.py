# -*- coding: utf-8 -*-
#
# HPX - dashboard
#
# Copyright (c) 2020 - ETH Zurich
# All rights reserved
#
# SPDX-License-Identifier: BSD-3-Clause

"""The data collection module is for storing the hpx performance counter in live
"""

from typing import Union

import numpy as np

from ...common.logger import Logger

logger = Logger()


class _NumpyArrayList:
    """This class allows for the growing of a numpy array of unknown size.

    Using np.append() for each DataCollection.add_line would be a waste ressources.
    This class is a wrapper around numpy arrays to allow for efficiently allocate and
    grow 2D numpy arrays.
    """

    def __init__(self, size_x, dtype):
        self.data = np.empty((100, size_x), dtype=dtype)
        self.capacity = 100
        self.size = 0
        self.size_x = size_x
        self.dtype = dtype

    def append(self, row):
        if self.size == self.capacity:
            self.capacity *= 2
            new_data = np.empty((self.capacity, self.size_x))
            new_data[: self.size] = self.data
            self.data = new_data

        self.data[self.size] = np.array(row, dtype=self.dtype)
        self.size += 1


def format_instance(locality_id, pool="default", thread_id=None, is_total=True):
    """"""
    if is_total:
        return str(locality_id)
    else:
        return (str(locality_id), str(pool), str(thread_id))


class DataCollection:
    """The data collection class provides an interface for storing and reading hpx performance data.

    """

    def __init__(self):
        self.data = {}
        # Contains also the task data
        self.task_data = {}

    def _add_instance_name(
        self, locality_id, pool="default", thread_id=None, is_total=True
    ) -> None:
        """Adds the instance name to the list of instance names stored in the class."""
        if not locality_id:
            return

        if locality_id not in self.task_data:
            self.task_data[str(locality_id)] = {}

        if is_total and "total" not in self.task_data[locality_id]:
            self.task_data[locality_id]["total"] = None
            return

        if pool not in self.task_data[locality_id]:
            self.task_data[locality_id][pool] = {}

        if thread_id not in self.task_data[locality_id][pool]:
            self.task_data[locality_id][pool][thread_id] = []

    def _get_instance_infos(self, full_instance: str) -> None:
        """"""
        if full_instance.startswith("/"):
            return None, None, None, None

        instance_split = full_instance.split("/")
        locality_id = instance_split[0].split("#")[1]
        thread_id = None
        pool = None
        is_total = False

        if "total" in instance_split[1]:
            is_total = True
        else:
            if len(instance_split) == 2:
                pool = "default"
                thread_id = instance_split[1].split("#")[1]
            else:
                pool = instance_split[1].split("#")[1]
                thread_id = instance_split[2].split("#")[1]

        return locality_id, pool, thread_id, is_total

    def add_task_data(self, locality, thread, name, begin, end):
        """"""
        self._add_instance_name(locality, thread_id=thread, is_total=False)
        self.task_data[locality]["default"][thread].append([name, float(begin), float(end)])

    def add_line(
        self,
        fullname: str,
        full_instance: str,
        parameters: Union[str, None],
        sequence_number: int,
        timestamp: float,
        timestamp_unit: str,
        value: str,
        value_unit: Union[str, None],
    ) -> None:
        """Adds a line of data to the DataCollection.

        Parameters
        ----------
        fullname
            complete name of the performance counter without the full instance name
            parameter
        parameters
            parameter(s) of the hpx performance counter
        full_instance
            counter instance name
        sequence_number
            sequence number of the counter invocation
        timestamp
            time stamp at which the information has been sampled
        timestamp_unit
            unit of the timestamp
        value
            actual counter value
            (could be simple number or multiple numbers separated by ':')
        value_unit
            unit of the counter value
        """
        name = fullname
        if parameters:
            name = fullname + "@" + parameters

        if name not in self.data:
            self.data[name] = {}

        locality_id, pool, thread_id, is_total = self._get_instance_infos(full_instance)

        instance_name = full_instance
        if locality_id:
            self._add_instance_name(locality_id, pool, thread_id, is_total)
            instance_name = format_instance(locality_id, pool, thread_id, is_total)

        try:
            value = float(value)
        except ValueError:
            value = str(value)

        line = [instance_name, int(sequence_number), timestamp, timestamp_unit, value, value_unit]
        if instance_name not in self.data[name]:
            self.data[name][instance_name] = []

        self.data[name][instance_name].append(line)

    def get_counter_names(self):
        """Returns the list of available counters that are currently in the collection."""
        return list(self.data.keys())

    def get_task_data(self, locality, worker, index=0):
        """"""
        if locality not in self.task_data:
            return np.array([])

        if "default" not in self.task_data[locality]:
            return np.array([])

        if worker not in self.task_data[locality]["default"]:
            return np.array([])

        if index >= len(self.task_data[locality]["default"][worker]):
            return np.array([])
        else:
            return np.array(self.task_data[locality]["default"][worker][index:])

    def get_data(self, fullname: str, instance_name: tuple, index=0):
        """"""
        if fullname not in self.data:
            return np.array([])

        if instance_name in self.data[fullname]:
            if index >= len(self.data[fullname][instance_name]):
                return np.array([])

            return np.array(self.data[fullname][instance_name][index:])
        else:
            return np.array([])

    def get_localities(self):
        """Returns the list of available localities that are currently in the collection"""
        return list(self.task_data.keys())

    def get_pools(self, locality):
        """Returns the list of available pools in a particular locality. The `total` is also
        counted as a pool.
        """
        if locality in self.task_data:
            pools = []
            for pool in self.task_data[locality].keys():
                if pool != "total" and pool:
                    pools.append(pool)
            return pools
        else:
            return []

    def get_num_worker_threads(self, locality):
        """Returns the number of worker threads in a particular locality"""
        num = 0
        if locality in self.task_data:
            for pool in self.task_data[locality].keys():
                if pool != "total" and pool:
                    for _ in self.task_data[locality][pool].keys():
                        num += 1

        return num

    def get_worker_threads(self, locality, pool):
        """Returns the list of worker threads in a particular locality and pool"""
        if locality in self.task_data:
            if pool in self.task_data[locality]:
                return list(self.task_data[locality][pool].keys())

        return []
