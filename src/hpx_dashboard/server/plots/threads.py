from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

import numpy as np

from .base_plot import BasePlot
from ..data_aggregator import DataAggregator
from ..data_collection import DataCollection


class ThreadsCount(BasePlot):
    """"""

    def __init__(self, doc, title="Instantaneous thread count", locality="0", threads="total"):
        """"""
        super().__init__(doc, title)
        self.plot = figure(title=title)
        self.data_aggregator = DataAggregator()
        self.last_run = -1
        self.instance_name = DataCollection.instance_infos_to_str(locality_id=locality)

        self.default_indices = {
            "all": 0,
            "active": 0,
            "pending": 0,
            "staged": 0,
            "suspended": 0,
            "terminated": 0,
        }
        self.data_sources = {}
        for name in self.default_indices.keys():
            self.data_sources[name] = ColumnDataSource({f"time_{name}": [], name: []})

        self.last_indices = self.default_indices

        self._build_data()

        colors = ["red", "blue", "green", "orange", "magenta", "black"]
        for i, name in enumerate(self.default_indices.keys()):
            self.plot.line(
                x=f"time_{name}",
                y=name,
                source=self.data_sources[name],
                legend_label=name,
                line_color=colors[i],
            )

    def _build_data(self):
        self.last_indices = self.default_indices

        if self.data_aggregator.current_data:
            for name in self.last_indices.keys():
                data = np.array(
                    self.data_aggregator.current_data["data"].get_data(
                        f"threads/count/instantaneous/{name}", self.instance_name
                    )
                )
                if data.ndim == 2:
                    self.last_indices[name] = data[-1, 1]
                    self.data_sources[name].data = {f"time_{name}": data[:, 2], name: data[:, 4]}

    def update(self):
        """"""
        if self.last_run != self.data_aggregator.last_run:
            self.last_run = self.data_aggregator.last_run
            self._build_data()
            return

        if self.data_aggregator.current_data:
            for name, index in self.last_indices.items():
                data = np.array(
                    self.data_aggregator.current_data["data"].get_data(
                        f"threads/count/instantaneous/{name}", self.instance_name, index,
                    )
                )
                if data.ndim == 2:
                    try:
                        self.last_indices[name] = data[-1, 1]
                    except:
                        print("hello", data.size)
                    self.data_sources[name].stream({f"time_{name}": data[:, 2], name: data[:, 4]})
