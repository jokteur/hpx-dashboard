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
        self._is_updating = {}
        self._last_run = -1
        self._data = {}
        self._periodic_callback = {}
        self._current_collection = None

    def _get_from_collection(self, doc, collection: DataCollection, identifier: tuple):
        """"""
        data_dict = {
            f"{identifier}_time": [],
            f"{identifier}": [],
        }
        if collection:

            data = collection.get_data(*identifier, self._data[doc][identifier]["last_index"])

            if data.ndim == 2:
                self._data[doc][identifier]["last_index"] = int(data[-1, 1])
                data_dict = {
                    f"{identifier}_time": data[:, 2],
                    f"{identifier}": data[:, 4].astype(float),
                }
        return data_dict

    def _update(self, doc):
        """"""
        reset = False
        if self._last_run != DataAggregator().last_run and DataAggregator().current_run:
            self._last_run = DataAggregator().last_run
            reset = True

        for identifier, data in self._data[doc].items():
            if reset:
                data["data_source"].data = self._get_from_collection(doc, None, identifier)
                data["last_index"] = 0
                data["last_time"] = 0
            if DataAggregator().current_data:
                new_data = self._get_from_collection(
                    doc, DataAggregator().current_data["data"], identifier
                )
                data_len = len(new_data[f"{identifier}"])
                if data_len > 0:
                    data["data_source"].stream(new_data)
                    data["last_time"] = new_data[f"{identifier}_time"][-1]

    def get_data(
        self,
        doc,
        counter_name: str,
        instance_id: tuple,
        only_live_collection=False,
        collection=None,
    ):
        """"""
        # Start auto-update if it is not already the case
        # self.start_update()

        identifier = (counter_name, instance_id)

        if doc not in self._data:
            self._data[doc] = {}
            self.start_update(doc)

        # Build the data source from scratch if it does not exists
        if identifier not in self._data[doc]:
            if not collection:
                if DataAggregator().current_data:
                    collection = DataAggregator().current_data
                elif DataAggregator().get_last_run() and not only_live_collection:
                    collection = DataAggregator().get_last_run()

            self._data[doc][identifier] = {
                "last_index": 0,
                "last_time": 0,
                "x_name": f"{identifier}_time",
                "y_name": f"{identifier}",
            }

            if collection:
                self._data[doc][identifier]["data_source"] = ColumnDataSource(
                    self._get_from_collection(doc, collection, identifier)
                )
            else:
                self._data[doc][identifier]["data_source"] = ColumnDataSource(
                    self._get_from_collection(doc, None, identifier)
                )

        return self._data[doc][identifier]

    def start_update(self, doc):
        """"""
        if doc not in self._is_updating:
            self._is_updating[doc] = False

        if not self._is_updating[doc]:
            self._periodic_callback = doc.add_periodic_callback(
                lambda: self._update(doc), self._refresh_rate
            )
            self._is_updating[doc] = True

    def stop_update(self, doc):
        """"""
        self._is_updating[doc] = False
        doc.remove_periodic_callback(self._periodic_callback)

    def set_refresh_rate(self, refresh_rate):
        """"""
        self._refresh_rate = refresh_rate
