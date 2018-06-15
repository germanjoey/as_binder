import re
import numpy

from bqplot import LinearScale, OrdinalColorScale, ColorAxis, Axis, Lines, Scatter, Figure
from ipywidgets import HBox, VBox, SelectionSlider, jslink, jsdlink, Layout, IntText, Label
from scipy import signal


fan_in = 10
header_re = re.compile(r'\D+(\d+)\D+(\d+\.\d+)/(\d+\.\d+)')
per_test_re = re.compile(r'\s*(\d+), (\d\.\d+)/(\d+\.\d+), (\d\.\d+E[\-+]\d+)')

def parse_degradation_results(filename):
    with open(filename) as f:
        lines = f.readlines()
    lines = [x.strip() for x in lines]

    i = 0
    results = {'x': {}, 'y': {}}

    while i < len(lines)-1:
        hm = header_re.match(lines[i])
        if hm is None:
            raise Exception("File Corruption on line %d for file %s" % (i, filename))
            
        (endpoints, mean_length, std_length) = (hm[1], hm[2], hm[3])

        #for j in range(1, 2):
        for j in range(1, fan_in+1):
            tm = per_test_re.match(lines[i+j])
            if tm is None:
                raise Exception("File Corruption on line %d for file %s: <%s>" % (i+j, filename, lines[i+j]))
            
            (tfan_in, mean_percent_traced, std_percent_traced, error) = (tm[1], tm[2], tm[3], tm[4])
            
            if tfan_in not in results['x']:
                results['x'][tfan_in] = []
                results['y'][tfan_in] = []
                
            results['x'][tfan_in].append(mean_length)
            results['y'][tfan_in].append(mean_percent_traced)

        i += (2 + fan_in)

    return results

def get_degradation_results(reservoir_size, sampling_target):
    rr = {}
    for sampler in ['uniform', 'normal']:
        filename = 'ss/degradation_results_%s_%d_%d.txt' % (
            sampler, reservoir_size, sampling_target)
        results = parse_degradation_results(filename)
        rr[sampler] = results
    return rr

def plot_degradation_results(reservoir_size=1000, sampling_target=10):
    x_sc = LinearScale(min=0)
    y_sc = LinearScale(min=0, max=1)

    ax_x = Axis(label='Average Trace Length', color='black',
                 scale=x_sc, grid_lines='solid')
    ax_y = Axis(label='Percent of sampled=True that were fully traced', scale=y_sc, side='left', grid_lines='solid',
                 orientation='vertical', color='black', tick_format=".0%")

    indices = ['1', '2', '3', '4', '6', '8', '10']
    colors = ['cyan', 'blue', 'green', 'orange', 'red', 'magenta', 'purple']
    details = list(zip(indices, colors))
    results = get_degradation_results(reservoir_size, sampling_target)

    marks = []
    for detail in details:
        index = detail[0]

        if index not in results['uniform']['x']:
            continue

        xd = [float(x) for x in results['uniform']['x'][index]]
        yd = [float(x) for x in results['uniform']['y'][index]]

        yz = list(zip(xd, list(yd)))
        ys = sorted(yz, key=lambda a: a[0])

        xdata = numpy.array([b[0] for b in ys])
        ydata = numpy.array([b[1] for b in ys])

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

        xdata_l = [b[0] for b in ys]
        ydata_s = signal.savgol_filter(ydata, 9, 3)
        ydata_b = numpy.zeros(len(ydata_s))

        line_mark = Lines(
            x=xdata_l,
            y=[ydata_s,ydata_b],
            colors = [detail[1],detail[1]],
            scales={'x': x_sc, 'y': y_sc},
            fill='between',
            fill_opacities=[0.9],
            stroke_width=1,
            enable_hover=True)
        marks.append(line_mark)

    fig = Figure(
        marks=marks,
        axes=[ax_x, ax_y],
        title='Degradation for Reservoir Size=%d and Sampling Target=%d' % (
            reservoir_size, sampling_target))

    display(fig)


def plot_comparison_degradation_results(reservoir_size=1000, sampling_target=10):
    x_sc = LinearScale(min=0)
    y_sc = LinearScale(min=0)

    ax_x = Axis(label='Average Trace Length', color='black',
                 scale=x_sc, grid_lines='solid')
    ax_y = Axis(label='Difference of sampled=True trace percentages', scale=y_sc, side='left', grid_lines='solid',
                 orientation='vertical', color='black', tick_format=".0%")

    indices = ['1', '2', '3', '4', '8']
    colors = ['cyan', 'blue', 'green', 'orange', 'magenta']
    details = list(zip(indices, colors))
    results = get_degradation_results(reservoir_size, sampling_target)

    marks = []
    for detail in details:
        index = detail[0]

        if index not in results['normal']['x']:
            continue

        xd = [float(x) for x in results['normal']['x'][index]]
        nr = numpy.array([float(x) for x in results['normal']['y'][index]])
        ur = numpy.array([float(x) for x in results['uniform']['y'][index]])

        yd = 2.0 * (nr - ur) / (nr + ur)
        yz = list(zip(xd, list(yd)))
        ys = sorted(yz, key=lambda a: a[0])

        xdata = numpy.array([b[0] for b in ys])
        ydata = numpy.array([b[1] for b in ys])

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

        xdata_l = [b[0] for b in ys]
        ydata_s = signal.savgol_filter(ydata, 11, 3)
        ydata_b = numpy.zeros(len(ydata_s))

        line_mark = Lines(
            x=xdata_l,
            y=[ydata_s, ydata_b],
            colors = [detail[1],detail[1]],
            scales={'x': x_sc, 'y': y_sc},
            fill='between',
            fill_opacities=[0.9],
            stroke_width=1,
            enable_hover=True)
        marks.append(line_mark)

    fig = Figure(
        marks=marks,
        axes=[ax_x, ax_y],
        legend_location='top-left',
        title='% extra traces lost, AS vs new AS')

    display(fig)