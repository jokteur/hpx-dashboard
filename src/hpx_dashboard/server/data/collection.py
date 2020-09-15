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

        for i, element in enumerate(row):
            self.data[self.size, i] = element
        self.size += 1

    def get(self):
        return self.data[: self.size, :]


def format_instance(locality_id, pool=None, thread_id="total"):
    """"""
    return (str(locality_id), pool, str(thread_id))


def from_instance(instance):
    """Returns the locality id, pool and thread id the str `instance`.
    If `instance` is not valid, then None is returned."""
    if isinstance(instance, tuple) or isinstance(instance, list):
        if not len(instance) == 3:
            return None

        if isinstance(instance, list):
            instance = tuple(instance)

        return instance
    elif isinstance(instance, str):
        return instance, None, "total"
    else:
        return None


class DataCollection:
    """
    The data collection class provides an interface for storing and reading hpx performance data"""

    _id_counter = 0

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.counter_info = {}
        self.data = {}
        # Task data is also used to identify all available instances
        self.task_data = {}

        # Variables for the growing numpy array
        self._line_to_hash = {}
        self._numpy_data = _NumpyArrayList(3, "float")
        self._id = self._id_counter
        self._id_counter += 1

    def _add_instance_name(self, locality_id, pool=None, thread_id=None) -> None:
        """Adds the instance name to the list of instance names stored in the class."""
        if not locality_id:
            return

        if locality_id not in self.task_data:
            self.task_data[str(locality_id)] = {}

        if pool not in self.task_data[locality_id]:
            self.task_data[locality_id][pool] = {}

        if thread_id not in self.task_data[locality_id][pool]:
            self.task_data[locality_id][pool][thread_id] = []

    def _get_instance_infos(self, full_instance: str) -> None:
        """"""
        if full_instance.startswith("/"):
            return None, None, None

        instance_split = full_instance.split("/")
        locality_id = instance_split[0].split("#")[1]
        thread_id = None
        pool = None

        if "total" in instance_split[1]:
            thread_id = "total"
        else:
            if len(instance_split) == 2:
                pool = None
                thread_id = instance_split[1].split("#")[1]
            elif "total" in instance_split[2]:
                pool = instance_split[1].split("#")[1]
                thread_id = "total"
            else:
                pool = instance_split[1].split("#")[1]
                thread_id = instance_split[2].split("#")[1]

        return locality_id, pool, thread_id

    def add_task_data(self, locality, thread, name, begin, end):
        """"""
        self._add_instance_name(locality, thread_id=thread)
        self.task_data[locality][None][thread].append([name, float(begin), float(end)])

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

        locality_id, pool, thread_id = self._get_instance_infos(full_instance)

        instance_name = full_instance
        if locality_id:
            self._add_instance_name(locality_id, pool, thread_id)
            instance_name = format_instance(locality_id, pool, thread_id)

        try:
            value = float(value)
        except ValueError:
            value = str(value)

        # Growing numpy array
        key = (self._id, name, instance_name)
        if key not in self._line_to_hash:
            self._line_to_hash[key] = float(len(self._line_to_hash.keys()))
        self._numpy_data.append([timestamp, value, self._line_to_hash[key]])

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

        if None not in self.task_data[locality]:
            return np.array([])

        if worker not in self.task_data[locality][None]:
            return np.array([])

        if index >= len(self.task_data[locality][None][worker]):
            return np.array([])
        else:
            return np.array(self.task_data[locality][None][worker][index:], dtype="O")

    def get_data(self, countername: str, instance_name: tuple, index=0):
        """"""
        if countername not in self.data:
            return np.array([])

        if instance_name in self.data[countername]:
            if index >= len(self.data[countername][instance_name]):
                return np.array([])

            return np.array(self.data[countername][instance_name][index:], dtype="O")
        else:
            return np.array([])

    def get_numpy_data(self):
        return self._numpy_data.get()

    def get_localities(self):
        """Returns the list of available localities that are currently in the collection"""
        return list(self.task_data.keys())

    def get_pools(self, locality):
        """Returns the list of available pools in a particular locality."""
        if locality in self.task_data:
            pools = []
            for pool in self.task_data[locality].keys():
                pools.append(pool)
            return pools
        else:
            return []

    def get_num_worker_threads(self, locality):
        """Returns the number of worker threads in a particular locality"""
        num = 0
        if locality in self.task_data:
            for pool in self.task_data[locality].keys():
                worker_list = [
                    int(idx) for idx in self.task_data[locality][pool].keys() if idx != "total"
                ]
                if worker_list:
                    num += max(worker_list) + 1
        return num

    def get_worker_threads(self, locality, pool=None):
        """Returns the list of worker threads in a particular locality and pool"""
        if locality in self.task_data:
            if pool in self.task_data[locality]:
                return [idx for idx in self.task_data[locality][pool].keys() if idx != "total"]

        return []

    def set_start_time(self, start_time):
        """Sets the start start of the collection."""
        self.start_time = start_time

    def set_end_time(self, end_time):
        """Sets the end time of the collection."""
        self.end_time = end_time

    def set_counter_infos(self, counter_info):
        """Sets the counter infos of the collection."""
        self.counter_info = counter_info

    def line_to_hash(self, countername, instance):
        """Returns the associated hashed countername and instance stored in the object."""

        key = (self._id, countername, instance)
        if key not in self._line_to_hash:
            self._line_to_hash[key] = float(len(self._line_to_hash.keys()))

        return self._line_to_hash[key]
