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

    def __init__(self, size_x, dtype, capacity=100):
        self.data = np.empty((capacity, size_x), dtype=dtype)
        self.capacity = capacity
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

    def replace(self, array):
        self.data = array
        self.capacity = len(array)
        self.size = len(array)

    def get(self):
        return self.data[: self.size, :]


def format_instance(locality, pool=None, worker_id="total"):
    """"""
    return (str(locality), pool, str(worker_id))


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

        self.timings = []
        self.line_timing = []

    def _add_instance_name(self, locality, pool=None, worker_id=None) -> None:
        """Adds the instance name to the list of instance names stored in the class."""
        if not locality:
            return

        if locality not in self.instances:
            self.instances[str(locality)] = {}

        if pool not in self.instances[locality]:
            self.instances[locality][pool] = {}

        if worker_id not in self.instances[locality][pool]:
            self.instances[locality][pool][worker_id] = []

    def _get_instance_infos(self, full_instance: str) -> None:
        """"""
        if full_instance.startswith("/"):
            return None, None, None

        instance_split = full_instance.split("/")
        locality = instance_split[0].split("#")[1]
        worker_id = None
        pool = None

        if "total" in instance_split[1]:
            worker_id = "total"
        else:
            if len(instance_split) == 2:
                pool = None
                worker_id = instance_split[1].split("#")[1]
            elif "total" in instance_split[2]:
                pool = instance_split[1].split("#")[1]
                worker_id = "total"
            else:
                pool = instance_split[1].split("#")[1]
                worker_id = instance_split[2].split("#")[1]

        return locality, pool, worker_id

    def add_task_data(
        self, locality, worker_id: int, name, start: float, end: float, initial_capacity=1000
    ):
        """Adds one task to the task data of the collection.

        This function also pre-builds the triangle mesh for the task plot that is used by datashader


        Arguments
        ---------
        locality : int
            locality index of the task
        worker_id : int
            id of the worker
        name : str
            name of the task
        start : float
            timestamp of the beginning of the task
        end : float
            timestamp of the end of the task
        initial_capacity : int
            size of the pre-allocated numpy array where the data will be stored
            (only used if this is the first the locality is encountered)
        """
        import time

        self._add_instance_name(locality, pool="default", worker_id=worker_id)

        if locality not in self._task_data:
            self._task_data[locality] = {
                "data": _NumpyArrayList(4, "float", initial_capacity),
                "verts": _NumpyArrayList(4, "float", initial_capacity * 4),
                "tris": _NumpyArrayList(3, np.int, initial_capacity * 2),
                "name_list": [],
                "name_set": set(),
                "min": np.finfo(float).max,
                "max": np.finfo(float).min,
                "workers": set(),
                "min_time": float(start),
            }

        worker_id = float(worker_id)
        start = float(start) - self._task_data[locality]["min_time"]
        end = float(end) - self._task_data[locality]["min_time"]

        if start < self._task_data[locality]["min"]:
            self._task_data[locality]["min"] = start
        if end > self._task_data[locality]["max"]:
            self._task_data[locality]["max"] = end

        top = worker_id + 1 / 2 * (1 - task_plot_margin)
        bottom = worker_id - 1 / 2 * (1 - task_plot_margin)

        self._task_data[locality]["name_list"].append(name)
        self._task_data[locality]["name_set"].add(name)
        self._task_data[locality]["workers"].add(worker_id)

        color_hash = int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16) % len(task_cmap)

        t = time.time()
        self._task_data[locality]["data"].append([worker_id, start, end, self._task_id])
        t1 = time.time() - t

        idx = self._task_data[locality]["verts"].size

        # Bottom left pt
        self._task_data[locality]["verts"].append([start, bottom, color_hash, self._task_id])
        # Top left pt
        self._task_data[locality]["verts"].append([start, top, color_hash, self._task_id])
        # Top right pt
        self._task_data[locality]["verts"].append([end, top, color_hash, self._task_id])
        # Bottom right pt

        self._task_data[locality]["verts"].append([end, bottom, color_hash, self._task_id])
        self._task_id += 1

        # Triangles
        self._task_data[locality]["tris"].append([idx, idx + 1, idx + 2])
        self._task_data[locality]["tris"].append([idx, idx + 2, idx + 3])

        self.timings.append([t1])

    def import_task_data(self, task_data):
        """Imports task data into the collection from a pandas DataFrame in one go.

        This function is there to speed-up import, but in fact does the same thing as add_task_data

        Arguments
        ---------
        task_data : pd.DataFrame
            dataframe that should have the columns `name`, `locality`, `worker_id`, `start` and
            `end`
        """

        df = task_data.groupby("locality", sort=False)
        for locality, group in df:
            locality = str(locality)
            min_time = group["start"].min()
            max_time = group["end"].max()
            self._task_data[locality] = {
                "data": _NumpyArrayList(4, "float"),
                "verts": _NumpyArrayList(4, "float"),
                "tris": _NumpyArrayList(3, np.int),
                "name_list": group["name"].to_list(),
                "min": min_time,
                "max": max_time,
                "workers": set(group["worker_id"].to_list()),
                "min_time": min_time,
            }
            for worker_id in self._task_data[locality]["workers"]:
                self._add_instance_name(locality, pool="default", worker_id=worker_id)

            self._task_data[locality]["name_set"] = set(self._task_data[locality]["name_list"])

            size = len(group)
            group["index"] = np.arange(size)
            group["color_hash"] = group["name"].apply(
                lambda name: int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16) % len(task_cmap)
            )

            group["top"] = group["worker_id"] + 1 / 2 * (1 - task_plot_margin)
            group["bottom"] = group["worker_id"] - 1 / 2 * (1 - task_plot_margin)

            # Build the vertices
            bottom_left = group[["start", "bottom", "color_hash", "index"]].rename(
                columns={"start": "x", "bottom": "y"}
            )
            top_left = group[["start", "top", "color_hash", "index"]].rename(
                columns={"start": "x", "top": "y"}
            )
            top_right = group[["end", "top", "color_hash", "index"]].rename(
                columns={"end": "x", "top": "y"}
            )
            bottom_right = group[["end", "bottom", "color_hash", "index"]].rename(
                columns={"end": "x", "bottom": "y"}
            )

            # Build the triangles indices
            group["v1"] = group["index"] + size
            group["v2"] = group["index"] + 2 * size
            group["v3"] = group["index"] + 3 * size

            tris_1 = group[["index", "v1", "v2"]].rename(columns={"index": "v0"})
            tris_2 = group[["index", "v2", "v3"]].rename(
                columns={"index": "v0", "v2": "v1", "v3": "v2"}
            )

            self._task_data[locality]["data"].replace(
                group[["worker_id", "start", "end", "index"]].to_numpy()
            )
            self._task_data[locality]["verts"].replace(
                pd.concat([bottom_left, top_left, top_right, bottom_right]).to_numpy()
            )
            self._task_data[locality]["tris"].replace(pd.concat([tris_1, tris_2]).to_numpy())

    def add_line(
        self,
        countername: str,
        instance: Union[tuple, str],
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
        countername
            complete name of the performance counter without the full instance name
            parameter
        parameters
            parameter(s) of the hpx performance counter
        instance
            counter instance name or tuple given by the format_instance function
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
        name = countername
        if parameters:
            name = countername + "@" + parameters

        if name not in self.data:
            self.data[name] = {}

        if isinstance(instance, tuple):
            locality, pool, worker_id = instance
        else:
            locality, pool, worker_id = self._get_instance_infos(instance)

        instance = instance
        if locality:
            self._add_instance_name(locality, pool, worker_id)
            instance = format_instance(locality, pool, worker_id)

        try:
            value = float(value)
        except ValueError:
            value = str(value)

        # Growing numpy array
        key = (self._id, name, instance)
        if key not in self._line_to_hash:
            self._line_to_hash[key] = float(len(self._line_to_hash.keys()))
        import time

        t = time.time()
        self._numpy_data.append([timestamp, value, self._line_to_hash[key]])
        self.line_timing.append(time.time() - t)

        line = [int(sequence_number), timestamp, timestamp_unit, value, value_unit]
        if instance not in self.data[name]:
            self.data[name][instance] = []

        self.data[name][instance].append(line)

    def get_counter_names(self):
        """Returns the list of available counters that are currently in the collection."""
        return list(self.data.keys())

    def task_mesh_data(self, locality):
        """"""
        if locality not in self._task_data:
            return [[0, 0, 0, 0]], [[0, 0, 0]], ((0, 1), (0, 1))

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

    def get_data(self, countername: str, instance: tuple, index=0):
        """Returns the data of the specified countername and the instance.

        Arguments
        ---------
        countername : str
            name of the HPX performance counter
        instance : tuple
            instance identifier (locality, pool, worker id) returned by the format_instance function
        index : int
            start from specified index

        Returns
        -------
        ndarray where the columns in order are sequence number, timestamp, timestamp unit,
        value and value unit
        """
        if countername not in self.data:
            return np.array([])

        if instance in self.data[countername]:
            if index >= len(self.data[countername][instance]):
                return np.array([])

            return np.array(self.data[countername][instance][index:], dtype="O")
        else:
            return np.array([])

    def line_data(self):
        return self._numpy_data.get()

    def task_data(self, locality):
        if locality not in self._task_data:
            return [], []
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
        """Returns the number of worker threads in a particular locality."""
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
        """Returns the list of worker threads in a particular locality and pool."""
        if locality in self.instances:
            if pool in self.instances[locality]:
                return [idx for idx in self.instances[locality][pool].keys() if idx != "total"]

        return []

    def export_counter_data(self):
        """Returns a pandas DataFrame that contains all the HPX performance counter data."""

        # Note: this is not the most efficient way to do this and for longer runs this can take a
        # few hundred of ms
        dfs = []
        for name in self.data.keys():
            for instance in self.data[name].keys():
                data = self.get_data(name, instance)
                df = pd.DataFrame(
                    data,
                    columns=[
                        "sequence_number",
                        "timestamp",
                        "timestamp_unit",
                        "value",
                        "value_unit",
                    ],
                )
                df["countername"] = name
                locality, pool, thread = from_instance(instance)
                df["locality"] = locality
                df["pool"] = pool
                df["thread"] = thread
                dfs.append(df)
        df = pd.concat(dfs).reset_index()
        del df["index"]
        return df

    def export_task_data(self):
        """Returns a pandas DataFrame that contains all the HPX task data."""
        dfs = []
        for locality in self.get_localities():
            task_data, task_names = self.task_data(locality)
            df = pd.DataFrame(task_data, columns=["worker_id", "start", "end", "name"])
            df = df.astype({"worker_id": int})
            df["locality"] = locality
            df["name"] = task_names
            dfs.append(df)
        return pd.concat(dfs)

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
