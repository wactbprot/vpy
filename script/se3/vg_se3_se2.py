import sys
import json
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
import matplotlib.pyplot as plt
from vpy.values import Pressure, Temperature, Error, Uncertainty, Sigma
font = {'family' : 'normal',
       # 'weight' : 'bold',
        'size'   : 18}

plt.rc('font', **font)

markers =("o", "D", "v", ">", "^", "1", "2", "3", "4")
colors = ('b', 'g', 'm', 'c', 'm', 'y', 'k', 'b', 'g')

io = Io()
se2_id_23 = 'cal-2018-se2-ik-4823_0005'
p_se2_23 = Pressure(io.get_doc_db(se2_id_23)).get_value('p_cor', 'mbar')*100
s_se2_23, _ = Sigma(io.get_doc_db(se2_id_23)).get_value_and_unit('eff')
u_se2_23= np.full( len(p_se2_23), 7.5e-4)

se2_id_25 = 'cal-2018-se2-ik-4825_0006'
p_se2_25 = Pressure(io.get_doc_db(se2_id_25)).get_value('p_cor', 'mbar')*100
s_se2_25, _ = Sigma(io.get_doc_db(se2_id_25)).get_value_and_unit('eff')
u_se2_25= np.full( len(p_se2_23), 7.5e-4)


##se3
se3_id_23_1 = 'cal-2018-se3-ik-4823_0003'
p_se3_23_1 = Pressure(io.get_doc_db(se3_id_23_1), quant='Analysis').get_value('ind_corr', 'Pa')
s_se3_23_1 = Error(io.get_doc_db(se3_id_23_1), quant='Analysis').get_value('ind', '1') +1
u_se3_23_1 = Uncertainty(io.get_doc_db(se3_id_23_1), quant='Analysis').get_value('total','1')

se3_id_25_1 = 'cal-2018-se3-ik-4825_0004'
p_se3_25_1 = Pressure(io.get_doc_db(se3_id_25_1), quant='Analysis').get_value('ind_corr', 'Pa')
s_se3_25_1 = Error(io.get_doc_db(se3_id_25_1), quant='Analysis').get_value('ind', '1') +1
u_se3_25_1 = Uncertainty(io.get_doc_db(se3_id_25_1), quant='Analysis').get_value('total','1')

se3_id_23_2 = 'cal-2018-se3-ik-4823_0001'
p_se3_23_2 = Pressure(io.get_doc_db(se3_id_23_2), quant='Analysis').get_value('ind_corr', 'Pa')
s_se3_23_2 = Error(io.get_doc_db(se3_id_23_2), quant='Analysis').get_value('ind', '1') +1
u_se3_23_2 = Uncertainty(io.get_doc_db(se3_id_23_2), quant='Analysis').get_value('total','1')

se3_id_25_2 = 'cal-2018-se3-ik-4825_0002'
p_se3_25_2 = Pressure(io.get_doc_db(se3_id_25_2), quant='Analysis').get_value('ind_corr', 'Pa')
s_se3_25_2 = Error(io.get_doc_db(se3_id_25_2), quant='Analysis').get_value('ind', '1') +1
u_se3_25_2 = Uncertainty(io.get_doc_db(se3_id_25_2), quant='Analysis').get_value('total','1')

se3_id_23_3 = 'cal-2018-se3-ik-4823_0004'
p_se3_23_3 = Pressure(io.get_doc_db(se3_id_23_3), quant='Analysis').get_value('ind_corr', 'Pa')
s_se3_23_3 = Error(io.get_doc_db(se3_id_23_3), quant='Analysis').get_value('ind', '1') +1
u_se3_23_3 = Uncertainty(io.get_doc_db(se3_id_23_3), quant='Analysis').get_value('total','1')

se3_id_25_3 = 'cal-2018-se3-ik-4825_0005'
p_se3_25_3 = Pressure(io.get_doc_db(se3_id_25_3), quant='Analysis').get_value('ind_corr', 'Pa')
s_se3_25_3 = Error(io.get_doc_db(se3_id_25_3), quant='Analysis').get_value('ind', '1') +1
u_se3_25_3 = Uncertainty(io.get_doc_db(se3_id_25_3), quant='Analysis').get_value('total','1')

plt.subplot(121)

plt.errorbar(p_se2_23 , s_se2_23,    yerr=u_se2_23  *2, marker = markers[1], linestyle="None", label="SE2 (18.10.18)", capsize=2, markersize=8, color=colors[0])
plt.errorbar(p_se3_23_1, s_se3_23_1, yerr=u_se3_23_1*2, marker = markers[2], linestyle="None", label="SE3 (01.10.18)", capsize=2, markersize=8, color=colors[1])
plt.errorbar(p_se3_23_3, s_se3_23_3, yerr=u_se3_23_3*2, marker = markers[4], linestyle="None", label="SE3 (15.10.18)", capsize=2, markersize=8, color=colors[2])

plt.xscale('symlog', linthreshx=1e-12)
plt.xlabel('Druck in Pa')
plt.ylabel('Akkommodationskoeffizient')
plt.title('Gasreibungsvakuummeter (№ 23)')
plt.xlim( (0.0005, 5) )
plt.legend()

plt.grid(True)

plt.subplot(122)

plt.errorbar(p_se2_25 , s_se2_25,    yerr=u_se2_25  *2, marker = markers[1], linestyle="None", label="SE2 (18.10.18)", capsize=2, markersize=8, color=colors[0])
plt.errorbar(p_se3_25_1, s_se3_25_1, yerr=u_se3_25_1*2, marker = markers[2], linestyle="None", label="SE3 (01.10.18)", capsize=2, markersize=8, color=colors[1])
plt.errorbar(p_se3_25_3, s_se3_25_3, yerr=u_se3_25_3*2, marker = markers[4], linestyle="None", label="SE3 (15.10.18)", capsize=2, markersize=8, color=colors[2])


plt.xscale('symlog', linthreshx=1e-12)
plt.xlabel('Druck in Pa')
plt.ylabel('Akkommodationskoeffizient')
plt.title('Gasreibungsvakuummeter (№ 25)')
plt.xlim( (0.0005, 5) )
plt.legend()

plt.grid(True)



plt.show()
