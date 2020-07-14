# -*- coding: utf-8 -*-
#
# HPX - dashboard
#
# Copyright (c) 2020 - ETH Zurich
# All rights reserved
#
# SPDX-License-Identifier: BSD-3-Clause

"""The data aggregator module is for storing any data coming from one or multiple hpx program runs.
"""

from typing import Union

from ..common.singleton import Singleton
from .data_collection import DataCollection


class DataAggregator(metaclass=Singleton):
    """DataAggregator is a singleton that store all the data from all the runs.
    """

    def __init__(self):
        """Initializes the data of the server."""
        self.data = []
        self.current_run = None
        self.last_run = None
        self.current_data = None
        self.dummy_counter = 0

    def new_collection(self, begin_time: float) -> None:
        """Adds a new DataCollection along with a timestamp to the aggregator.

        Parameters
        ----------
        begin_time
            time of the beginning of the collection
            (should be sent by the hpx-dashboard agent)
        """
        self.data.append(
            {
                "begin-time": begin_time,
                "end-time": None,
                "data": DataCollection(),
                "counter-info": None,
            }
        )
        self.current_run = len(self.data) - 1
        self.current_data = self.data[self.current_run]

    def set_counter_infos(self, counter_infos: dict):
        """Sets the counter informations of the current collection.

        If there is no active collection, this function does nothing

        Parameters
        ----------
        counter_infos
            dictionnary of descriptions for each available counter of the hpx application
        """
        if self.current_run is not None:
            self.data[self.current_run]["counter-info"] = counter_infos

    def get_last_run(self) -> Union[DataCollection, None]:
        """Returns the last active DataCollection.
        If there was no active collection, None is returned.
        """
        if self.last_run is not None:
            return self.data[self.last_run]
        else:
            return None

    def finalize_current_collection(self, end_time: float) -> None:
        """Finalizes the current collection of data

        Parameters
        ----------
        end_time
            time of when the collection has finished"""
        self.data[self.current_run]["end-time"] = end_time
        self.last_run = self.current_run
        self.current_data = None
        self.current_run = None
