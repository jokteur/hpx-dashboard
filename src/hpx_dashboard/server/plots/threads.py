from bokeh.plotting import figure

from .base_plot import BasePlot
from ..data import DataSources, DataAggregator, format_instance

data_aggregator = DataAggregator()
data_sources = DataSources()


class ThreadsPlot(BasePlot):
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
            title=title, width=980, height=300, x_axis_label="time (s)", y_axis_label="Thread count"
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


class Memory(BasePlot):
    def __init__(
        self, doc, title="Memory usage", locality="0",
    ):
        """"""
        super().__init__(doc, title)
        self.layout = figure(
            title=title,
            width=980,
            height=300,
            x_axis_label="time (s)",
            y_axis_label="Memory usage (bytes)",
        )

        counter_name = "runtime/memory/resident"

        data = data_sources.get_data(counter_name, "0")

        self.layout.line(
            x=data["x_name"], y=data["y_name"], source=data["data_source"],
        )
