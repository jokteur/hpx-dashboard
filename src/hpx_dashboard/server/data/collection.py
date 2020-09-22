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
import hashlib

import numpy as np
import pandas as pd

from ...common.logger import Logger
from ...common.constants import task_cmap, task_plot_margin

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

        # Task data
        self._task_data = {}
        self._task_id = 0

        self.instances = {}

        # Variables for the growing numpy array
        self._line_to_hash = {}
        self._numpy_data = _NumpyArrayList(3, "float")
        self._id = self._id_counter
        self._id_counter += 1

    def _add_instance_name(self, locality_id, pool=None, thread_id=None) -> None:
        """Adds the instance name to the list of instance names stored in the class."""
        if not locality_id:
            return

        if locality_id not in self.instances:
            self.instances[str(locality_id)] = {}

        if pool not in self.instances[locality_id]:
            self.instances[locality_id][pool] = {}

        if thread_id not in self.instances[locality_id][pool]:
            self.instances[locality_id][pool][thread_id] = []

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

    def add_task_data(self, locality, thread_id: int, name, begin: float, end: float):
        """"""
        self._add_instance_name(locality, thread_id=thread_id)

        if locality not in self._task_data:
            self._task_data[locality] = {
                "data": _NumpyArrayList(4, "float"),
                "verts": _NumpyArrayList(4, "float"),
                "tris": _NumpyArrayList(3, np.int),
                "name_list": [],
                "name_set": set(),
                "min": np.finfo(float).max,
                "max": np.finfo(float).min,
                "workers": set(),
                "min_time": float(begin),
            }

        thread_id = float(thread_id)
        begin = float(begin) - self._task_data[locality]["min_time"]
        end = float(end) - self._task_data[locality]["min_time"]

        if begin < self._task_data[locality]["min"]:
            self._task_data[locality]["min"] = begin
        if end > self._task_data[locality]["max"]:
            self._task_data[locality]["max"] = end

        top = thread_id + 1 / 2 * (1 - task_plot_margin)
        bottom = thread_id - 1 / 2 * (1 - task_plot_margin)

        self._task_data[locality]["name_list"].append(name)
        self._task_data[locality]["name_set"].add(name)
        self._task_data[locality]["workers"].add(thread_id)

        color_hash = int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16) % len(task_cmap)

        self._task_data[locality]["data"].append([thread_id, begin, end, self._task_id])

        idx = len(self._task_data[locality]["verts"].get())

        # Bottom left pt
        self._task_data[locality]["verts"].append([begin, bottom, color_hash, self._task_id])
        # Top left pt
        self._task_data[locality]["verts"].append([begin, top, color_hash, self._task_id])
        # Top right pt
        self._task_data[locality]["verts"].append([end, top, color_hash, self._task_id])
        # Bottom right pt
        self._task_data[locality]["verts"].append([end, bottom, color_hash, self._task_id])
        self._task_id += 1

        # Triangles
        self._task_data[locality]["tris"].append([idx, idx + 1, idx + 2])
        self._task_data[locality]["tris"].append([idx, idx + 2, idx + 3])

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

    def get_task_mesh_data(self, locality):
        """"""
        if locality not in self._task_data:
            return [[0, 0, 0]], [[0, 0, 0]], ((0, 1), (0, 1))

        # Find the plot ranges
        max_worker_id = max(self._task_data[locality]["workers"])
        min_time = self._task_data[locality]["min"]
        max_time = self._task_data[locality]["max"]

        vertices = pd.DataFrame(
            self._task_data[locality]["verts"].get(), columns=["x", "y", "z", "patch_id"]
        )
        triangles = pd.DataFrame(
            self._task_data[locality]["tris"].get().astype(int), columns=["v0", "v1", "v2"]
        )
        x_range = (min_time, max_time)
        y_range = (-1 + task_plot_margin, max_worker_id + 1 / 2 * (1 - task_plot_margin))
        return vertices, triangles, (x_range, y_range)

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

    def get_task_data(self, locality):
        if locality not in self._task_data:
            return []
        return self._task_data[locality]["data"].get(), self._task_data[locality]["name_list"]

    def get_task_names(self, locality):
        if locality not in self._task_data:
            return set()

        return self._task_data[locality]["name_set"]

    def get_localities(self):
        """Returns the list of available localities that are currently in the collection"""
        return list(self.instances.keys())

    def get_pools(self, locality):
        """Returns the list of available pools in a particular locality."""
        if locality in self.instances:
            pools = []
            for pool in self.instances[locality].keys():
                pools.append(pool)
            return pools
        else:
            return []

    def get_num_worker_threads(self, locality):
        """Returns the number of worker threads in a particular locality"""
        num = 0
        if locality in self.instances:
            for pool in self.instances[locality].keys():
                worker_list = [
                    int(idx) for idx in self.instances[locality][pool].keys() if idx != "total"
                ]
                if worker_list:
                    num += max(worker_list) + 1
        return num

    def get_worker_threads(self, locality, pool=None):
        """Returns the list of worker threads in a particular locality and pool"""
        if locality in self.instances:
            if pool in self.instances[locality]:
                return [idx for idx in self.instances[locality][pool].keys() if idx != "total"]

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
