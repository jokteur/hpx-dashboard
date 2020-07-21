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

from abc import ABCMeta

from bokeh.models import ColumnDataSource

from ...common.singleton import Singleton
from ..data_aggregator import DataAggregator
from ..data_collection import DataCollection

data_aggregator = DataAggregator()


class DataSources(metaclass=Singleton):
    """"""

    def __init__(self, refresh_rate=100):
        """"""
        self.refresh_rate = refresh_rate
        self.is_updating = False
        self.subscribers = {}
        self.last_run = -1
        self.data = {}

    def _get_from_collection(self, collection: DataCollection, identifier: tuple):
        """"""
        data_dict = {
            f"{identifier}_time": [],
            f"{identifier}": [],
        }
        if collection:
            data = collection["data"].get_data(*identifier, self.data[identifier]["last_index"])

            if data.ndim == 2:
                self.data[identifier]["last_index"] = int(data[-1, 1])
                data_dict = {
                    f"{identifier}_time": data[:, 2],
                    f"{identifier}": data[:, 4].astype(float),
                }
        return data_dict

    def get_data(self, counter_name: str, instance_id: tuple, only_live_collection=False):
        """"""
        identifier = (counter_name, instance_id)
        # Build the data source from scratch if it does not exists
        if identifier not in self.data:
            collection = None
            if data_aggregator.current_data:
                collection = data_aggregator.current_data
            elif data_aggregator.get_last_run() and not only_live_collection:
                collection = data_aggregator.get_last_run()

            self.data[identifier] = {
                "last_index": 0,
                "x_name": f"{identifier}_time",
                "y_name": f"{identifier}",
            }

            if collection:
                self.data[identifier]["data_source"] = ColumnDataSource(
                    self._get_from_collection(collection, identifier)
                )
            else:
                self.data[identifier]["data_source"] = ColumnDataSource(
                    self._get_from_collection(None, identifier)
                )

        return self.data[identifier]

    def start_update(self, doc):
        """"""
        if not self.is_updating:
            self.current_doc = doc
            doc.add_periodic_callback(self.update, self.refresh_rate)
            self.is_updating = True
        # else:
        #     self.current_doc.remove_periodic_callback(self.update)
        #     self.current_doc = doc
        #     doc.add_periodic_callback(self.update, self.refresh_rate)

    def stop_update(self):
        """"""
        self.is_updating = False
        self.current_doc.remove_periodic_callback(self.update)

    def set_refresh_rate(self, refresh_rate):
        """"""
        self.refresh_rate = refresh_rate

    def update(self):
        """"""
        reset = False
        if self.last_run != data_aggregator.last_run and data_aggregator.current_run:
            self.last_run = data_aggregator.last_run
            reset = True

        for identifier, data in self.data.items():
            if reset:
                data["data_source"].data = self._get_from_collection(None, identifier)
            if data_aggregator.current_data:
                data["data_source"].stream(
                    self._get_from_collection(data_aggregator.current_data, identifier)
                )


class BasePlot(metaclass=ABCMeta):
    """"""

    def __init__(self, doc, title, refresh_rate=100):
        """"""
        self.plot = None
        self.title = title
        self.buffer = None
        self.refresh_rate = refresh_rate
        self.doc = doc

    def start_update(self):
        self.doc.add_periodic_callback(self.update, self.refresh_rate)

    def stop_update(self):
        self.doc.remove_periodic_callback(self.update)

    def update(self):
        pass

    def get_plot(self):
        return self.plot
