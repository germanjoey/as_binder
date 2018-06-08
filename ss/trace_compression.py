from bqplot import LinearScale, OrdinalColorScale, ColorAxis, Axis, Lines, Scatter, Figure
from ipywidgets import HBox, VBox, SelectionSlider, jslink, jsdlink, Layout, IntText, Label

def plot_compression_results(xdata, raw_results):
    avg_results = []

    for d in xdata:
        data = raw_results[d]
        avg = sum(data) / len(data)
        avg_results.append(avg)

    x_sc = LinearScale(min=0, max=250)
    y_sc = LinearScale(min=0, max=1)

    ax_x = Axis(label='Path Length',
                 scale=x_sc, grid_lines='solid')
    ax_y = Axis(label='Average Rate of Compression', scale=y_sc, side='left', grid_lines='solid',
                 orientation='vertical')
    mark = Lines(
        x=xdata,
        y=avg_results,
        colors = ['blue'],
        scales={'x': x_sc, 'y': y_sc},
        enable_hover=True)

    display(Figure(marks=[mark], axes=[ax_x, ax_y], title='Span Reservoir Compression Rate'))