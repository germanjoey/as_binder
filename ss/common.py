import numpy

def logspace_int(nmin, nmax, num_points):
    return numpy.logspace(
        numpy.log10(nmin),
        numpy.log10(nmax),
        num=num_points,
        dtype=int)


def linspace_fractions_noninclusive(num_points):
    delta_fraction = 1.0/num_points

    return numpy.linspace(
        delta_fraction,
        1.0 - delta_fraction,
        num_points - 1)