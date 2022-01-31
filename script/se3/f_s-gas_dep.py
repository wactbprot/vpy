import sys
sys.path.append(".")

import json
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
import matplotlib.pyplot as plt
from vpy.values import Expansion, Temperature, Error, Uncertainty, Pressure
font = {'family' : 'normal',
        #'weight' : 'bold',
        'size'   : 12
        }

plt.rc('font', **font)

io = Io()
plt.subplot(111)

s = -10
e = -1
f_n2_1 = Expansion(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0001').get("Calibration").get("Analysis")).get_value('f_s', '1')[s:e]
p_n2_1 = Pressure(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0001').get("Calibration").get("Analysis")).get_value('cal', 'mbar')[s:e]

f_n2_2 = Expansion(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0003').get("Calibration").get("Analysis")).get_value('f_s', '1')[s:e]
p_n2_2 = Pressure(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0003').get("Calibration").get("Analysis")).get_value('cal', 'mbar')[s:e]

f_he_1 = Expansion(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0004').get("Calibration").get("Analysis")).get_value('f_s', '1')[s:e]
p_he_1 = Pressure(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0004').get("Calibration").get("Analysis")).get_value('cal', 'mbar')[s:e]

f_he_2 = Expansion(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0005').get("Calibration").get("Analysis")).get_value('f_s', '1')[s:e]
p_he_2 = Pressure(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0005').get("Calibration").get("Analysis")).get_value('cal', 'mbar')[s:e]

f_ar_1 = Expansion(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0006').get("Calibration").get("Analysis")).get_value('f_s', '1')[s:e]
p_ar_1 = Pressure(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0006').get("Calibration").get("Analysis")).get_value('cal', 'mbar')[s:e]

f_ar_2 = Expansion(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0007').get("Calibration").get("Analysis")).get_value('f_s', '1')[s:e]
p_ar_2 = Pressure(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0007').get("Calibration").get("Analysis")).get_value('cal', 'mbar')[s:e]


f_n2_m = (np.mean(f_n2_2) + np.mean(f_n2_1))/2.
f_he_m = (np.mean(f_he_2) + np.mean(f_he_1))/2.
f_ar_m = (np.mean(f_ar_2) + np.mean(f_ar_1))/2.

#plt.axhline(y=f_n2_m/f_n2_m-1, xmin=0.5, xmax=0.90, linewidth=2.5, color='blue', alpha=0.2)
#plt.axhline(y=f_he_m/f_n2_m-1, xmin=0.5, xmax=0.90, linewidth=2.5, color='red', alpha=0.2)
#plt.axhline(y=f_ar_m/f_n2_m-1, xmin=0.5, xmax=0.90, linewidth=2.5, color='orange' ,alpha=0.2)

plt.text(0.9,f_n2_m/f_n2_m-1 ,"$f_{} = {}$".format("{N2}",np.round(f_n2_m, 8)), bbox=dict(facecolor='blue', alpha=0.1), fontsize=12)
plt.text(0.9,f_he_m/f_n2_m-1 ,"$f_{} = {}$".format("{He}",np.round(f_he_m, 8)), bbox=dict(facecolor='red', alpha=0.1), fontsize=12)
plt.text(0.9,f_ar_m/f_n2_m-1 ,"$f_{} = {}$".format("{Ar}",np.round(f_ar_m, 8)), bbox=dict(facecolor='orange', alpha=0.1), fontsize=12)

plt.plot(p_n2_1, f_n2_1/f_n2_m-1, label="N$_2$ 1st meas.", marker='s', linestyle=":", markersize=10, color="blue")
plt.plot(p_n2_1, f_n2_2/f_n2_m-1, label="N$_2$ 2nd meas.", marker='8', linestyle=":", markersize=10, color="blue")
plt.plot(p_he_1, f_he_1/f_n2_m-1, label="He 1st meas.", marker='s', linestyle=":", markersize=10, color="red")
plt.plot(p_he_2, f_he_2/f_n2_m-1, label="He 2nd meas.", marker='8', linestyle=":", markersize=10, color="red")
plt.plot(p_ar_1, f_ar_1/f_n2_m-1, label="Ar 1st meas.", marker='s', linestyle=":", markersize=10, color="orange")
plt.plot(p_ar_2, f_ar_2/f_n2_m-1, label="Ar 2nd meas.", marker='8', linestyle=":", markersize=10, color="orange")

plt.legend(fontsize=12)
plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
#plt.title('successive expansion measurement of $f_s$\n(nitrogen, helium, argon)')
plt.xlabel('$p_{frs} - p_{nd}$ in mbar')
plt.ylabel('$f_s/\\overline{f_{N2}}-1$')
plt.grid(True)
plt.savefig("f_s-var_gas.pdf", orientation='landscape', papertype='a4',)
plt.show()
