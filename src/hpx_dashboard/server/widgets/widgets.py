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

import copy
from datetime import datetime

from bokeh.layouts import column, row
from bokeh.models.widgets import Button, Div, Toggle

from .base import BaseWidget, empty_placeholder
from ..plots import generator
from .select import DataCollectionSelect, SelectCustomLine
from ..data import DataAggregator


class CustomCounterWidget(BaseWidget):
    """Produces a widget for plotting any counters"""

    def __init__(self, doc, refresh_rate=1000, collection=None, **kwargs):
        """Produces a widget that allows the user to add / remove plots for any
        counters from any collection

        Arguments
        ---------
        doc : Bokeh Document
            bokeh document for auto-updating the widget
        refresh_rate : int
            refresh rate at which the Select refreshes and checks for new data collections (in ms)
        **kwargs
            arguments for the bokeh Select widget
        """
        super().__init__(doc, refresh_rate=refresh_rate, collection=collection, **kwargs)

        self._defaults_opts = dict(plot_width=800, plot_height=300)
        self._defaults_opts.update((key, value) for key, value in kwargs.items())

        self._plots = [
            generator.TimeSeries(
                doc, refresh_rate=refresh_rate, title="Plot 1", **self._defaults_opts
            )
        ]
        self._lines = {}
        self._lines_info = set()
        self._line_counter = 0

        # Buttons for editing the lines
        self._add_line_b = Button(label="+", width=40)
        self._add_line_b.on_click(self._add_line)

        # Buttons for adding and removing plots
        self._add_plot_b = Button(label="+", width=40)
        self._add_plot_b.on_click(self._add_plot)

        self._remove_plot_b = Button(label="-", width=40)
        self._remove_plot_b.on_click(self._remove_plot)

        # For editing the lines
        self._edit_button = Toggle(label="Edit lines", width=100)
        self._edit_button.on_click(self._toggle_edit)

        self._root = column(
            row(
                Div(text="Add or remove plots:"),
                self._remove_plot_b,
                self._add_plot_b,
                self._edit_button,
            ),
            empty_placeholder(),
            column(self._plots[-1].layout()),
        )

    def _remove_line(self, idx):
        del self._lines[idx]
        self._update_line_widget()

    def _add_line(self):
        plots_text = [f"Plot {i + 1}" for i, _ in enumerate(self._plots)]
        self._line_counter += 1
        self._lines[self._line_counter] = SelectCustomLine(
            self._doc, self._line_counter, plots_text, self._remove_line,
        )
        self._update_line_widget()

    def _update_plots(self):
        plots = [plot.layout() for plot in self._plots]
        self._root.children[2] = column(*plots)

        # Update the lines with the available plots
        plots_text = [f"Plot {i + 1}" for i, _ in enumerate(self._plots)]
        for line in self._lines.values():
            line.set_plots(plots_text)

    def _update_line_widget(self):
        lines = [line.layout() for line in self._lines.values()]
        self._root.children[1] = column(row(self._add_line_b, Div(text="Add line")), *lines)

    def _toggle_edit(self, edit):
        if edit:
            self._update_line_widget()
        else:
            self._root.children[1] = empty_placeholder()

    def _add_plot(self):
        opts = copy.deepcopy(self._defaults_opts)
        self._plots.append(
            generator.TimeSeries(
                self._doc,
                refresh_rate=self._refresh_rate,
                title=f"Plot {len(self._plots) + 1}",
                **opts,
            )
        )
        self._update_plots()

    def update(self):
        lines = set()
        noname_lines = set()
        for line in self._lines.values():
            prop = line.properties()
            noname_lines.add(prop[:-1])
            lines.add(prop)

        deleted_lines = self._lines_info.difference(lines)
        new_lines = lines.difference(self._lines_info)

        for plot_id, collection, countername, instance, name in deleted_lines:
            # They may be multiple lines (with different names) in lines that have the same
            # (countername, instance, collection). If we delete one of this line
            # in the plot as there are still identical lines in the set (without looking at names),
            # we may end up deleting a line that still needs to be plotted.
            # noname_lines allows to check for that
            if (plot_id, collection, countername, instance) not in noname_lines and len(
                self._plots
            ) >= plot_id:
                self._plots[plot_id - 1].remove_line(countername, instance, collection)

        for plot_id, collection, countername, instance, name in new_lines:
            self._plots[plot_id - 1].add_line(countername, instance, collection, name)
        self._lines_info = lines

    def _remove_plot(self):
        if len(self._plots) == 1:
            return
        del self._plots[-1]
        self._update_plots()


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
        self._selected_collection = None
        self._select = DataCollectionSelect(doc, self._set_collection, refresh_rate=refresh_rate)
        self._div = Div(text="<b>No data available</b>")
        self._root = column(self._select.layout(), self._div)

    def _set_collection(self, collection):
        """"""
        self._selected_collection = collection
        self._callback(collection)
        self.update()

    def update(self):
        super().update()

        collection = None
        most_recent_flag = False
        if not self._selected_collection:
            most_recent_flag = True
            collection = self._select_last_collection()
        else:
            collection = self._selected_collection

        if collection:
            collection_list = DataAggregator().data
            index = collection_list.index(collection)
            collection = collection_list[index]

            # Title of the run
            title = f"Run #{index}"

            if DataAggregator().get_current_run() == collection:
                if most_recent_flag:
                    title += " (most recent, live)"
                else:
                    title += " (live)"
            elif most_recent_flag:
                title += " (most recent)"

            # Timings of the run
            begin_time = datetime.fromtimestamp(int(collection.start_time))
            time_info = f"<em>Start</em>: {begin_time}<br />"
            if collection.end_time:
                end_time = datetime.fromtimestamp(int(collection.end_time))
                time_info += f"<em>End</em>: {end_time}"

            # Num threads and localities
            localities = collection.get_localities()
            num_workers = 0
            if localities:
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
