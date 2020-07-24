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

from bokeh.models import ColumnDataSource

from ...common.singleton import Singleton
from ...common.logger import Logger
from .aggregator import DataAggregator
from .collection import DataCollection

logger = Logger()


class DataSources(metaclass=Singleton):
    """This class allows for the creation of ColumnDataSource needed for plotting with Bokeh.

    The user can call the get_data() method to get a ColumnDataSource instance of the desired
    performance counter and counter instance."""

    def __init__(self, refresh_rate=100):
        """"""
        self._refresh_rate = refresh_rate
        self._is_updating = False
        self._last_run = -1
        self._data = {}
        self._periodic_callback = None

    def _get_from_collection(self, collection: DataCollection, identifier: tuple):
        """"""
        data_dict = {
            f"{identifier}_time": [],
            f"{identifier}": [],
        }
        if collection:
            data = collection["data"].get_data(*identifier, self._data[identifier]["last_index"])

            if data.ndim == 2:
                self._data[identifier]["last_index"] = int(data[-1, 1])
                data_dict = {
                    f"{identifier}_time": data[:, 2],
                    f"{identifier}": data[:, 4].astype(float),
                }
        return data_dict

    def _update(self):
        """"""
        reset = False
        if self._last_run != DataAggregator().last_run and DataAggregator().current_run:
            self._last_run = DataAggregator().last_run
            reset = True

        for identifier, data in self._data.items():
            if reset:
                data["data_source"].data = self._get_from_collection(None, identifier)
                data["last_index"] = 0
            if DataAggregator().current_data:
                data["data_source"].stream(
                    self._get_from_collection(DataAggregator().current_data, identifier)
                )

    def get_data(
        self, counter_name: str, instance_id: tuple, only_live_collection=False, collection=None
    ):
        """"""
        # Start auto-update if it is not already the case
        # self.start_update()

        identifier = (counter_name, instance_id)
        # Build the data source from scratch if it does not exists
        if identifier not in self._data:
            if not collection:
                if DataAggregator().current_data:
                    collection = DataAggregator().current_data
                elif DataAggregator().get_last_run() and not only_live_collection:
                    collection = DataAggregator().get_last_run()

            self._data[identifier] = {
                "last_index": 0,
                "x_name": f"{identifier}_time",
                "y_name": f"{identifier}",
            }

            if collection:
                self._data[identifier]["data_source"] = ColumnDataSource(
                    self._get_from_collection(collection, identifier)
                )
            else:
                self._data[identifier]["data_source"] = ColumnDataSource(
                    self._get_from_collection(None, identifier)
                )

        return self._data[identifier]

    def start_update(self, doc):
        """"""
        if not self._is_updating:
            self._doc = doc
            self._periodic_callback = doc.add_periodic_callback(self._update, self._refresh_rate)
            self._is_updating = True

    def stop_update(self):
        """"""
        self._is_updating = False
        self._doc.remove_periodic_callback(self._periodic_callback)

    def set_refresh_rate(self, refresh_rate):
        """"""
        self._refresh_rate = refresh_rate
        # self.stop_update()
        # self.start_update()
