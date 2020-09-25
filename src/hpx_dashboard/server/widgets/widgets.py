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
import json

from bokeh.layouts import column, row
from bokeh.models.widgets import Button, Div, Toggle, TextAreaInput

from .base import BaseWidget, empty_placeholder
from ..plots import generator
from .select import DataCollectionSelect, SelectCustomLine
from ...common.logger import Logger
from ..data import DataAggregator, from_instance

logger = Logger()


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

        self._lines = {}
        self._lines_info = set()
        self._line_counter = 0

        # Buttons for editing the lines
        self._add_line_b = Button(label="+", width=40)
        self._add_line_b.on_click(self._add_line)

        # Toggle button for the shading of the plots
        self._shade_b = Toggle(label="Toggle plot shading", width=150)
        self._shade_b.on_click(self._toggle_shade)

        # Buttons for adding and removing plots
        self._add_plot_b = Button(label="+", width=40)
        self._add_plot_b.on_click(self._add_plot)

        self._remove_plot_b = Button(label="-", width=40)
        self._remove_plot_b.on_click(self._remove_plot)

        # For editing the lines
        self._edit_button = Toggle(label="Edit lines", width=100)
        self._edit_button.on_click(self._toggle_edit)

        self._json_input = TextAreaInput(
            title="Export / inport widget:", width=500, max_length=20000
        )
        self._json_update_button = Button(label="Update from input", width=150)
        self._json_update_button.on_click(self._set_from_input)

        self._save_button = Button(label="Save state of widget to session", width=170)
        self._save_button.on_click(self._save_widget)

        self._root = column(
            row(
                Div(text="Add or remove plots:"),
                self._remove_plot_b,
                self._add_plot_b,
                self._edit_button,
                self._shade_b,
                self._save_button,
            ),
            empty_placeholder(),
            empty_placeholder(),
        )

        self._plots = []
        self._add_plot()

        # If there is a saved state in the session of the widget
        json_txt = DataAggregator().get_custom_widget_config()
        if json_txt:
            self.from_json(json_txt)

    def _remove_line(self, idx):
        del self._lines[idx]
        self._update_line_widget()

    def _add_line(self, update=True):
        plots_text = [f"Plot {i + 1}" for i, _ in enumerate(self._plots)]
        self._line_counter += 1
        self._lines[self._line_counter] = SelectCustomLine(
            self._doc,
            self._line_counter,
            plots_text,
            self._remove_line,
        )
        if update:
            self._update_line_widget()

    def _toggle_shade(self, shade):
        for plot in self._plots:
            plot.toggle_shade()

    def _save_widget(self):
        DataAggregator().set_custom_widget_config(json.loads(self.to_json()))

    def _update_plots(self):
        plots = [plot.layout() for plot in self._plots]
        self._root.children[2] = column(*plots)

        # Update the lines with the available plots
        plots_text = [f"Plot {i + 1}" for i, _ in enumerate(self._plots)]
        for line in self._lines.values():
            line.set_plots(plots_text)

    def _update_line_widget(self):
        lines = [line.layout() for line in self._lines.values()]
        self._root.children[1] = column(
            row(self._json_input, self._json_update_button),
            row(self._add_line_b, Div(text="Add line")),
            *lines,
        )

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

    def _set_from_input(self):
        self._toggle_edit(False)
        self._edit_button.active = False
        self.from_json(self._json_input.value)

    def to_json(self):
        """Converts the state of the widget (number of plots, lines) to json"""
        json_dict = {"num_plots": len(self._plots), "lines": []}
        for plot_id, _, countername, instance, name in self._lines_info:
            json_dict["lines"].append(
                {"plot_id": plot_id, "countername": countername, "instance": instance, "name": name}
            )
        return json.dumps(json_dict)

    def from_json(self, json_txt):
        """Takes a json as input and generates the corresponding plots and widgets.
        Returns True if successful, False otherwise."""
        json_dict = {}
        try:
            json_dict = json.loads(json_txt.rstrip())
        except json.decoder.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e.msg}")

        if "lines" not in json_dict:
            return False

        num_plots = 1
        if "num_plots" in json_dict:
            num_plots = json_dict["num_plots"]

        # Remove all the lines
        self._lines.clear()

        # Set the correct number of plots
        if num_plots > len(self._plots):
            for _ in range(num_plots - len(self._plots)):
                self._add_plot()
        elif num_plots < len(self._plots):
            for _ in range(len(self._plots) - num_plots):
                self._remove_plot()

        for line in json_dict["lines"]:
            if not isinstance(line, dict):
                return False
            if (
                "plot_id" not in line
                or "countername" not in line
                or "instance" not in line
                or "name" not in line
            ):
                return False

            if not from_instance(tuple(line["instance"])):
                return False

            locality_id, pool, thread_id = from_instance(line["instance"])

            self._add_line(False)
            self._lines[self._line_counter].set_properties(
                line["plot_id"],
                None,
                line["countername"],
                locality_id,
                pool,
                thread_id,
                line["name"],
            )

        return True

    def update(self):
        lines = set()
        for line in self._lines.values():
            lines.add(line.properties())

        deleted_lines = self._lines_info.difference(lines)
        new_lines = lines.difference(self._lines_info)

        for plot_id, collection, countername, instance, name in deleted_lines:
            if len(self._plots) >= plot_id:
                self._plots[plot_id - 1].remove_line(
                    countername, instance, collection, name, hold_update=True
                )

        for plot_id, collection, countername, instance, name in new_lines:
            self._plots[plot_id - 1].add_line(
                countername, instance, collection, name, hold_update=True
            )

        for plot in self._plots:
            plot._make_figure()

        self._lines_info = lines

        self._json_input.value = self.to_json()

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
            collection = DataAggregator().get_live_collection()
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
