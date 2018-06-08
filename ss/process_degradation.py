import re
from bqplot import LinearScale, OrdinalColorScale, ColorAxis, Axis, Lines, Scatter, Figure
from ipywidgets import HBox, VBox, SelectionSlider, jslink, jsdlink, Layout, IntText, Label

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

        for j in range(1, fan_in+1):
            tm = per_test_re.match(lines[i+j])
            if tm is None:
                raise Exception("File Corruption on line %d for file %s" % (i+j, filename))
            
            (tfan_in, mean_percent_traced, std_percent_traced, error) = (tm[1], tm[2], tm[3], tm[4])
            
            if tfan_in not in results['x']:
                results['x'][tfan_in] = []
                results['y'][tfan_in] = []
                
            results['x'][tfan_in].append(mean_length)
            results['y'][tfan_in].append(mean_percent_traced)

        i += (2 + fan_in)

    return results

def plot_degradation_results(reservoir_size=1000, sampling_target=10):
    filename = 'ss/degradation_results_%d_%d.txt' % (reservoir_size, sampling_target)
    results = parse_degradation_results(filename)

    x_sc = LinearScale(min=0, max=250)
    y_sc = LinearScale(min=0, max=1)

    ax_x = Axis(label='Average Path Length',
                 scale=x_sc, grid_lines='solid')
    ax_y = Axis(label='Percent of sampled=True fully traced', scale=y_sc, side='left', grid_lines='solid',
                 orientation='vertical')

    indices = ['1', '2', '3', '4', '6', '8', '10']
    colors = ['blue', 'cyan', 'green', 'yellow', 'red', 'magenta', 'purple']
    details = list(zip(indices, colors))
    details.reverse()

    marks = []
    for detail in details:
        index = detail[0]
        mark = Scatter(
            x=results['x'][index],
            y=results['y'][index],
            colors = [detail[1]],
            scales={'x': x_sc, 'y': y_sc},
            labels=['Fan In=%s' % index],
            enable_hover=True,
            display_legend=True)
        marks.append(mark)

    display(
        Figure(
            marks=marks,
            axes=[ax_x, ax_y],
            title='Degradation for Reservoir Size=%d and Sampling Target=%d' % (
                reservoir_size, sampling_target)))
