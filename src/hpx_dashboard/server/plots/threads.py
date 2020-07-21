from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

from .base_plot import BasePlot, DataSources
from ..data_aggregator import DataAggregator
from ..data_collection import format_instance

data_aggregator = DataAggregator()
data_sources = DataSources()


class Threads2(BasePlot):
    def __init__(
        self,
        doc,
        title="Instantaneous thread count",
        locality="0",
        pool="default",
        thread_id=None,
        is_total=True,
    ):
        """"""
        super().__init__(doc, title)
        self.plot = figure(
            title=title, width=980, x_axis_label="time (s)", y_axis_label="Thread count"
        )
        self.data_aggregator = DataAggregator()

        self.names = {
            "all": "black",
            "active": "green",
            "pending": "blue",
            "staged": "magenta",
            "suspended": "orange",
            "terminated": "red",
        }

        for name, color in self.names.items():
            counter_name = f"threads/count/instantaneous/{name}"
            instance_id = format_instance(locality, pool, thread_id, is_total)

            data = data_sources.get_data(counter_name, instance_id)

            self.plot.line(
                x=data["x_name"],
                y=data["y_name"],
                legend_label=name,
                line_color=color,
                source=data["data_source"],
            )

        data_sources.start_update(self.doc)


class Memory(BasePlot):
    def __init__(
        self, doc, title="Memory usage", locality="0",
    ):
        """"""
        super().__init__(doc, title)
        self.plot = figure(
            title=title, width=980, x_axis_label="time (s)", y_axis_label="Memory usage (bytes)"
        )
        self.data_aggregator = DataAggregator()

        counter_name = "runtime/memory/resident"
        # instance_id = format_instance(locality)

        data = data_sources.get_data(counter_name, "0")

        self.plot.line(
            x=data["x_name"], y=data["y_name"], source=data["data_source"],
        )


class ThreadsCount(BasePlot):
    """"""

    def __init__(
        self,
        doc,
        title="Instantaneous thread count",
        locality="0",
        pool="default",
        thread_id="0",
        is_total=False,
    ):
        """"""
        super().__init__(doc, title)
        self.plot = figure(title=title, width=980)
        self.data_aggregator = DataAggregator()
        self.last_run = -1
        self.instance_name = format_instance(locality, pool, thread_id, True)

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
                data = self.data_aggregator.current_data["data"].get_data(
                    f"threads/count/instantaneous/{name}", self.instance_name
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
                data = self.data_aggregator.current_data["data"].get_data(
                    f"threads/count/instantaneous/{name}", self.instance_name, index,
                )
                if data.ndim == 2:
                    self.last_indices[name] = data[-1, 1]
                    self.data_sources[name].stream({f"time_{name}": data[:, 2], name: data[:, 4]})
