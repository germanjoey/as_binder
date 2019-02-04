import re
import numpy

from bqplot import LinearScale, OrdinalColorScale, ColorAxis, Axis, Lines, Scatter, Figure
from ipywidgets import HBox, VBox, SelectionSlider, jslink, jsdlink, Layout, IntText, Label
from scipy import signal

from process_degradation import parse_degradation_results, diff_result_set

fan_in = 10
header_re = re.compile(r'\D+(\d+)\D+(\d+\.\d+)/(\d+\.\d+)')
per_test_re = re.compile(r'\s*(\d+), (\d\.\d+)/(\d+\.\d+), (\d\.\d+E[\-+]\d+)')

def get_real_degradation_results(name):
    rr = {}
    for sampler in ['expbackoff', 'adaptive']:
        filename = 'ss/data_results/%s/%s.txt' % (sampler, name)
        results = parse_degradation_results(filename)
        rr[sampler] = results
    return rr

def plot_real_comparison_degradation_results(name):
    x_sc = LinearScale(min=0, max=260)
    y_sc = LinearScale(min=0, max=0.2)

    ax_x = Axis(label='Average Trace Length', color='black',
                 scale=x_sc, grid_lines='solid')
    ax_y = Axis(label='Difference of sampled=True trace percentages', scale=y_sc, side='left', grid_lines='solid',
                 orientation='vertical', color='black', tick_format=".0%")

    indices = ['1', '2', '3', '4', '8']
    colors = ['cyan', 'blue', 'green', 'orange', 'magenta']
    details = list(zip(indices, colors))
    results = get_real_degradation_results(name)

    marks = []
    for detail in details:
        index = detail[0]

        if index not in results['adaptive']['x']:
            continue

        xdata, ydata = diff_result_set(results, index, 'adaptive', 'expbackoff')

        scatter_mark = Scatter(
            x=xdata,
            y=ydata,
            colors = [detail[1]],
            scales={'x': x_sc, 'y': y_sc},
            labels=['Fan In=%s' % index],
            enable_hover=True,
            default_size=12,
            display_legend=True)
        marks.append(scatter_mark)

        xdata_l = xdata
        ydata_s = signal.savgol_filter(ydata, 25, 3)
        ydata_b = numpy.zeros(len(ydata_s))

        line_mark = Lines(
            x=xdata_l,
            y=[ydata_s, ydata_b],
            colors = [detail[1],detail[1]],
            scales={'x': x_sc, 'y': y_sc},
            fill='between',
            fill_opacities=[0.8],
            stroke_width=1,
            enable_hover=True)
        marks.append(line_mark)

    fig = Figure(
        marks=marks,
        axes=[ax_x, ax_y],
        legend_location='top-right',
        title='% extra traces gained, proposed AS - current AS')

    display(fig)