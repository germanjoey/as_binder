import os
import os.path
import re
import sys
import glob
import numpy

root_path = '/Users/jryan/Documents/as_binder'
sys.path.insert(0, root_path)

from scipy.stats import lognorm
from ss.process_degradation import diff_result_set, parse_degradation_results


expected_size = 1000
fan_ins = [str(x+1) for x in range(10)]
srx = re.compile(r'(\d+)\.txt')
sampler_types = {'adaptive', 'expbackoff'}
ln = lognorm(1, scale=14.333, loc=-1)


results = {}
for filename in glob.glob("%s/ss/data_results/adaptive/*.txt" % root_path):
    name = srx.findall(filename)[0]

    if name not in ['000000', '2314731', '4345270', '2638951', '4132727', '828085', '2350895', '2638956', '2066188', '4120950', '2679406', '2155560']:
        continue

    found = True
    for sampler_type in sampler_types:
        filename = "%s/ss/data_results/%s/%s.txt" % (root_path, sampler_type, name)
        if not os.path.exists(filename):
            found = False
            continue

    if not found:
        continue

    full = True
    temp_results = {}
    try:
        for sampler_type in sampler_types:
            filename = "%s/ss/data_results/%s/%s.txt" % (root_path, sampler_type, name)
            temp_results[sampler_type] = parse_degradation_results(filename)

        for fan_in in fan_ins:
            if len(temp_results[sampler_type]['x'][fan_in]) != expected_size:
                full = False
                continue
    except:
        full = False

    if not full:
        continue

    results[name] = []
    for fan_in in fan_ins:
        xdata, ydata = diff_result_set(temp_results, fan_in, 'adaptive', 'expbackoff')

        total = 0.0
        prob_total = 0.0
        for x, y in zip(xdata, ydata):
            prob = ln.pdf(x)
            prob_total += prob
            total += prob * y

        results[name].append(total / prob_total)

names = [(x, max(results[x])) for x in results.keys()]
sorted_names = [x[0] for x in sorted(names, key=lambda a: a[1])]

for name in sorted_names:
    print(name, " ".join(['%5.3f' % x for x in results[name]]))
