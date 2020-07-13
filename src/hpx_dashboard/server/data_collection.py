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

    def add_line(
        self,
        fullname: str,
        parameters: Union[str, None],
        full_instance: str,
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

        line = [sequence_number, timestamp, timestamp_unit, value, value_unit]
        if full_instance not in self.data[name]:
            self.data[name][full_instance] = [line]
        else:
            self.data[name][full_instance].append(line)
