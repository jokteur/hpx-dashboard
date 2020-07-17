from bokeh.layouts import column

# from bokeh.models import Button
# from bokeh.palettes import RdYlBu3
# from bokeh.plotting import figure

from .plots.threads import ThreadsCount


def app(doc):
    threads_count = ThreadsCount(doc)

    # put the button and plot in a layout and add to the document
    p = threads_count.get_plot()
    doc.add_root(column(p))
    return p
