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

from datetime import datetime

from bokeh.layouts import column
from bokeh.models.widgets import Button, Div

from .base import BaseWidget, empty_placeholder
from .select import DataCollectionSelect, SelectCounter
from ..data import DataAggregator

# from ..plots import PlotGenerator


class DataCollectionWidget(BaseWidget):
    """Produces a widget for selecting current and past data collection instances"""

    def __init__(self, doc, callback, refresh_rate=500, **kwargs):
        """Produces a widget that shows all the current and past data collection instances
        in the form of a Select.

        Arguments
        ---------
        doc : Bokeh Document
            bokeh document for auto-updating the widget
        callback : function(collection: DataCollection)
            callback for notifying when the user selects a certain data collection
        refresh_rate : int
            refresh rate at which the Select refreshes and checks for new data collections (in ms)
        **kwargs
            arguments for the bokeh Select widget
        """
        super().__init__(doc, callback, refresh_rate=refresh_rate, **kwargs)
        self._collection = None
        self._select = DataCollectionSelect(doc, self._set_collection, refresh_rate=refresh_rate)
        self._div = Div(text="<b>No run selected</b>")
        self._root = column(self._select.layout(), self._div)

    def _set_collection(self, collection):
        """"""
        self._collection = collection
        self._callback(collection)
        self._update_widget()

    def _update_widget(self):
        if self._collection:
            collection_list = DataAggregator().data
            index = collection_list.index(self._collection)
            collection = collection_list[index]

            # Title of the run
            title = f"Run #{index}"
            if DataAggregator().get_current_run() == self._collection:
                title += " (live)"

            # Timings of the run
            begin_time = datetime.fromtimestamp(int(collection.start_time))
            time_info = f"<em>Start</em>: {begin_time}<br />"
            if collection.end_time:
                end_time = datetime.fromtimestamp(int(collection.end_time))
                time_info += f"<em>End</em>: {end_time}"

            # Num threads and localities
            localities = collection.get_localities()
            num_workers = collection.get_num_worker_threads(localities[0])

            instance_info = ""
            if len(localities) == 1:
                instance_info += "1 locality"
            else:
                instance_info += f"{len(localities)} localities"

            instance_info += "<br />"

            if num_workers == 1:
                instance_info += "1 thread per locality"
            else:
                instance_info += f"{num_workers} threads per locality"

            text = f"""<span class="run_summary"><h3 class="run_title">{title}</h3><br />
            {time_info}<br />
            {instance_info}</span>"""

            if text != self._div.text:
                self._div.text = text


class PlotGeneratorWidget(BaseWidget):
    """"""

    def __init__(self, doc, callback, refresh_rate=500, **kwargs):
        """Produces a widget that allows for selecting a particular counter and instance in a certain run.

        Arguments
        ---------
        doc : Bokeh Document
            bokeh document for auto-updating the widget
        callback : function(collection: DataCollection)
            callback for notifying when the user selects a certain data collection
        collection : DataCollection
            instance of data collection to search for the available counters
        refresh_rate : int
            refresh rate at which the widget refreshes itself
        **kwargs
            arguments for the bokeh Select widgets
        """
        super().__init__(doc, callback, refresh_rate=refresh_rate)

        # self.plot = PlotGenerator(doc, "Line plot", width=980, height=500)

        self.add_button = Button("Add counter")
        self.ok_button = Button("Ok")
        self.add_button.on_click(self._add_button_click)
        self.ok_button.on_click(self._ok_button_click)

        self.selected_locality = None
        self.selected_collection = None
        self.selected_instance = None

        self._root = column(self.add_button, empty_placeholder(), self.plot.get_plot())

    def _selected(self, out):
        print(out)

    def _add_button_click(self):
        self._root.children[1] = column(SelectCounter(self._doc, self._selected), self.ok_button)

    def _ok_button_click(self):
        pass
