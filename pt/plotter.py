import numpy
from bqplot import LinearScale, LogScale, OrdinalColorScale, ColorAxis, Axis, Figure, Lines, Hist
from ipywidgets import HBox, VBox, FloatSlider, FloatLogSlider, SelectionSlider
from functools import wraps

color_choices = ['Blue', 'Red', 'Green', 'Purple', 'Orange', 'Cyan', 'Magenta']

__default_plotter_options = {}
def set_default_plotter_options(new_defaults):
    global __default_plotter_options
    for key in new_defaults:
        __default_plotter_options[key] = new_defaults[key]

class memoize(dict):
    def __init__(self, func):
        self.func = func
    
    def __call__(self, *args):
        return self[args]

    def __missing__(self, key):
        result = self[key] = self.func(*key)
        return result

def vectorize(f):
    @wraps(f)
    def wrapper(x, **kwargs):
        try:
            return numpy.array([f(_, **kwargs) for _ in iter(x)])
        except TypeError:
            return f(x, **kwargs)
    return wrapper

def set_plot_opts(kwargs):
    for key in ['ysc_min', 'ysc_max']:
        if key not in kwargs:        
            kwargs[key] = None
            
    for key in ['ax', 'ay', 'title']:
        if key not in kwargs:        
            kwargs[key] = ''
            
    if 'yscale' not in kwargs:
        kwargs['yscale'] = LinearScale
    if 'xscale' not in kwargs:
        kwargs['xscale'] = LinearScale
    if 'mark_type' not in kwargs:
        kwargs['mark_type'] = 'lines'

def hline(val):
    def line_func(x, **kwargs):
        return numpy.ones(len(x))*val
    return line_func

def make_quick_plot(xdata, *gen, defaults=None, **kwargs):
    set_plot_opts(kwargs)

    if defaults is None:
        defaults = {}

    x_sc = kwargs['xscale'](min=min(xdata), max=max(xdata))
    y_sc = kwargs['yscale'](min=kwargs['ysc_min'], max=kwargs['ysc_max'])
    ax_x = Axis(label=kwargs['ax'], scale=x_sc, grid_lines='solid')
    ax_y = Axis(label=kwargs['ay'], scale=y_sc, orientation='vertical', side='left', grid_lines='solid')
    
    lines = []

    for i,g in enumerate(gen):
        data = g(xdata, **defaults)
        if kwargs['mark_type'] == 'lines':
            mark = Lines(
                x=xdata,
                y=data,
                colors=[color_choices[i]],
                scales={'x': x_sc, 'y': y_sc},
                stroke_width=4,
                visible=True)
        elif kwargs['mark_type'] == 'hist':
            mark = Hist(
                sample=data,
                colors=[color_choices[i]],
                scales={'x': x_sc, 'y': y_sc},
                stroke_width=4,
                visible=True)
        else:
            raise Exception("WRONG")

        lines.append(mark)

    ymark = None
    if 'vline' in kwargs:
        v = kwargs['vline']
        ymin = min([min(l.y) for l in lines])
        ymax = max([max(l.y) for l in lines])

        ymark = Lines(
            x=[v, v],
            y=[ymin, ymax],
            colors=['black'],
            scales={'x': x_sc, 'y': y_sc},
            visible=True)
        lines.insert(0, ymark)

    sliders = {}
    for s in defaults:
        slider = SelectionSlider(
            value=defaults[s],
            options=__default_plotter_options[s],
            description=s.title(),
            readout=True)
        sliders[s] = slider

    def on_change(change):
        values = {}
        for slider in sliders:
            values[slider] = sliders[slider].value
        
        for g,l in zip(gen, lines):
            if kwargs['mark_type'] == 'hist':
                l.samples = g(xdata, **values)
            else:
                l.y = g(xdata, **values)

        if ymark is not None:
            ymin = min([min(l.y) for l in lines])
            ymax = max([max(l.y) for l in lines])
            ymark.y = [ymin, ymax]
            
        ax_y.scale = y_sc

        if 'trim_yscale' in values:
            if not values['trim_yscale']:
                y_sc.max = None
            else:
                y_sc.max = 1

    def get_value(name):
        return sliders[name].value
        
    for slider in sliders:
        sliders[slider].observe(on_change, names='value')
        
    fig = Figure(marks=lines, axes=[ax_x, ax_y], title=kwargs['title'])

    setattr(fig, 'get_value', get_value)
    display(VBox([*sliders.values()]), fig)

    return fig