import sys
import json
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
import matplotlib.pyplot as plt
from vpy.values import Expansion, Temperature, Error, Uncertainty, Pressure
font = {'family' : 'normal',
        'weight' : 'bold',
        'size'   : 18}

plt.rc('font', **font)

io = Io()
plt.subplot(111)

s = -10
e = -1
f_n2_1 = Expansion(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0001').get("Calibration").get("Analysis")).get_value('f_s', '1')[s:e]
p_n2_1 = Pressure(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0001').get("Calibration").get("Analysis")).get_value('cal', 'mbar')[s:e]
plt.plot(p_n2_1, f_n2_1, label="N2 M1", marker='s', linestyle=":", markersize=10, color="blue")

<<<<<<< HEAD
f_n2_1 = Expansion(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0001').get("Calibration").get("Analysis")).get_value('f_s', '1')[-9:-1]
p_n2_1 = Pressure(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0001').get("Calibration").get("Analysis")).get_value('cal', 'mbar')[-9:-1]
u_n2_1 = Uncertainty(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0001').get("Calibration").get("Analysis")).get_value('total', '1')[-9:-1]
plt.errorbar(p_n2_1, f_n2_1,  yerr=u_n2_1 *f_n2_1/2, label="N2 M1", marker='s', linestyle=":", markersize=10)

f_n2_2 = Expansion(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0003').get("Calibration").get("Analysis")).get_value('f_s', '1')[-9:-1]
p_n2_2 = Pressure(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0003').get("Calibration").get("Analysis")).get_value('cal', 'mbar')[-9:-1]
u_n2_2 = Uncertainty(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0003').get("Calibration").get("Analysis")).get_value('total', '1')[-9:-1]
plt.errorbar(p_n2_2, f_n2_2,  yerr=u_n2_2 *f_n2_2/2, label="N2 M2", marker='s', linestyle=":", markersize=10)

f_he_1 = Expansion(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0004').get("Calibration").get("Analysis")).get_value('f_s', '1')[-9:-1]
p_he_1 = Pressure(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0004').get("Calibration").get("Analysis")).get_value('cal', 'mbar')[-9:-1]
u_he_1 = Uncertainty(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0004').get("Calibration").get("Analysis")).get_value('total', '1')[-9:-1]
plt.errorbar(p_he_1, f_he_1,  yerr=u_he_1 *f_he_1/2, label="He M1", marker='8', linestyle=":", markersize=10)

f_he_2 = Expansion(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0005').get("Calibration").get("Analysis")).get_value('f_s', '1')[-9:-1]
p_he_2 = Pressure(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0005').get("Calibration").get("Analysis")).get_value('cal', 'mbar')[-9:-1]
u_he_2 = Uncertainty(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0005').get("Calibration").get("Analysis")).get_value('total', '1')[-9:-1]
plt.errorbar(p_he_2, f_he_2,  yerr=u_he_2 *f_he_2/2, label="He M2", marker='8', linestyle=":", markersize=10)
=======
f_n2_2 = Expansion(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0003').get("Calibration").get("Analysis")).get_value('f_s', '1')[s:e]
p_n2_2 = Pressure(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0003').get("Calibration").get("Analysis")).get_value('cal', 'mbar')[s:e]
plt.plot(p_n2_1, f_n2_2, label="N2 M2", marker='8', linestyle=":", markersize=10, color="blue")

f_he_1 = Expansion(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0004').get("Calibration").get("Analysis")).get_value('f_s', '1')[s:e]
p_he_1 = Pressure(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0004').get("Calibration").get("Analysis")).get_value('cal', 'mbar')[s:e]
plt.plot(p_he_1, f_he_1, label="He M1", marker='s', linestyle=":", markersize=10, color="red")

f_he_2 = Expansion(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0005').get("Calibration").get("Analysis")).get_value('f_s', '1')[s:e]
p_he_2 = Pressure(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0005').get("Calibration").get("Analysis")).get_value('cal', 'mbar')[s:e]
plt.plot(p_he_2, f_he_2, label="He M2", marker='8', linestyle=":", markersize=10, color="red")

f_ar_1 = Expansion(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0006').get("Calibration").get("Analysis")).get_value('f_s', '1')[s:e]
p_ar_1 = Pressure(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0006').get("Calibration").get("Analysis")).get_value('cal', 'mbar')[s:e]
plt.plot(p_ar_1, f_ar_1, label="Ar M1", marker='s', linestyle=":", markersize=10, color="orange")

f_ar_2 = Expansion(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0007').get("Calibration").get("Analysis")).get_value('f_s', '1')[s:e]
p_ar_2 = Pressure(io.get_doc_db('cal-2019-se3|frs5-vg-1001_0007').get("Calibration").get("Analysis")).get_value('cal', 'mbar')[s:e]
plt.plot(p_ar_2, f_ar_2, label="Ar M2", marker='8', linestyle=":", markersize=10, color="orange")
>>>>>>> 1de96852b1a72e15e1a824cee3148819dae2b592

plt.legend()
plt.title('SE3 expansion $f_s$ (Nitrogen, Helium, Argon)')
plt.xlabel('$p_{frs} - p_{nd}$ in mbar')
plt.ylabel('$f_s$')
plt.grid(True)
plt.show()