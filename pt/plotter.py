import numpy
from bqplot import LinearScale, LogScale, OrdinalColorScale, ColorAxis, Axis, Lines, Figure
from ipywidgets import HBox, VBox, FloatSlider, FloatLogSlider, SelectionSlider
from functools import wraps

color_choices = ['Blue', 'Red', 'Green', 'Purple']

default_options = {}
def set_default_plotter_options(new_defaults):
    global default_options
    for key in new_defaults:
        default_options[key] = new_defaults[key]

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

def make_quick_plot(xdata, *gen, defaults=None, **kwargs):
    set_plot_opts(kwargs)
    
    x_sc = kwargs['xscale'](min=min(xdata), max=max(xdata))
    y_sc = kwargs['yscale'](min=kwargs['ysc_min'], max=kwargs['ysc_max'])
    ax_x = Axis(label=kwargs['ax'], scale=x_sc, grid_lines='solid')
    ax_y = Axis(label=kwargs['ay'], scale=y_sc, orientation='vertical', side='left', grid_lines='solid')
    
    lines = []

    for i,g in enumerate(gen):
        line = Lines(
            x=xdata,
            y=g(xdata, **defaults),
            colors=[color_choices[i]],
            scales={'x': x_sc, 'y': y_sc},
            stroke_width=4,
            visible=True)
        lines.append(line)

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
            options=default_options[s],
            description=s.title(),
            readout=True)
        sliders[s] = slider

    def on_change(change):
        values = {}
        for slider in sliders:
            values[slider] = sliders[slider].value
        
        for g,l in zip(gen, lines):
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
        
    for slider in sliders:
        sliders[slider].observe(on_change, names='value')

        
    fig = Figure(marks=lines, axes=[ax_x, ax_y], title=kwargs['title'])
    display(VBox([*sliders.values()]), fig)
    return fig