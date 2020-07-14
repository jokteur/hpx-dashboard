from bokeh.layouts import column
from bokeh.models import Button
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure

from .data_aggregator import DataAggregator


def app(doc):
    # create a plot and style its properties
    p = figure(x_range=(0, 100), y_range=(0, 100), toolbar_location=None)
    p.border_fill_color = "black"
    p.background_fill_color = "black"
    p.outline_line_color = None
    p.grid.grid_line_color = None

    # add a text renderer to our plot (no data yet)
    r = p.text(
        x=[],
        y=[],
        text=[],
        text_color=[],
        text_font_size="26px",
        text_baseline="middle",
        text_align="center",
    )

    ds = r.data_source

    i = 0

    # create a callback that will add a number in a random location
    def callback():
        # BEST PRACTICE --- update .data in one step with a new dict
        nonlocal i
        data_aggregator = DataAggregator()
        new_data = dict()
        new_data["x"] = [30]
        new_data["y"] = [30]
        new_data["text_color"] = [RdYlBu3[i % 3]]
        new_data["text"] = [str(data_aggregator.dummy_counter)]
        ds.data = new_data
        i += 1

    # add a button widget and configure with the call back
    button = Button(label="Update")
    button.on_click(callback)

    # put the button and plot in a layout and add to the document
    doc.add_root(column(button, p))
    doc.add_periodic_callback(callback, 100)
    return p
