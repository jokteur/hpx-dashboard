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


class DataCollection:
    """The data collection class provides an interface for storing and reading hpx performance data.

    """

    def __init__(self):
        self.data = {}
        self.instances = {}

    def _get_instance_infos(self, full_instance: str) -> None:
        """"""
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
                thread_id = instance_split[2].split("#")[2]

        return locality_id, thread_id, pool, is_total

    def _add_instance_name(
        self, locality_id, thread_id=None, pool="default", is_total=True
    ) -> None:
        """Adds the instance name to the list of instance names stored in the class."""
        if locality_id not in self.instances:
            self.instances[locality_id] = {}

        if is_total and "total" not in self.instances[locality_id]:
            self.instance[locality_id]["total"] = None
            return

        if pool not in self.instances[locality_id]:
            self.instances[locality_id][pool] = {}

        if thread_id not in self.instances[locality_id][pool]:
            self.instances[locality_id][pool][thread_id] = None

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

        line = [full_instance, sequence_number, timestamp, timestamp_unit, value, value_unit]
        if full_instance not in self.data[name]:
            self.data[name][full_instance] = [line]
        else:
            self.data[name][full_instance].append(line)

        if not full_instance.startswith("/") and "locality" in full_instance:
            self._add_instance_name(full_instance)

    def get_counter_names(self):
        """"""
        return list(self.data.keys())

    def get_data(self, fullname: str, full_instance="*"):
        """"""

        if fullname not in self.data:
            return None

        # Wildcard `*` has been used
        result = []
        if "*" in full_instance:
            for key in self.data[fullname].keys():
                if full_instance.split("*")[0] in key:
                    result += self.data[fullname][key]
        else:
            if full_instance in self.data[fullname]:
                result = self.data[fullname][full_instance]
            else:
                result = None

        return result
