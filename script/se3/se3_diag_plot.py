"""
python script/se3/se3_diag_plot.py --ids 'cal-2019-se3-ik-4556_0001'  
"""
import sys
import os
sys.path.append(os.environ["VIRTUAL_ENV"])

import json
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis

from vpy.values import Pressure, Temperature, Error, Uncertainty, Expansion
from vpy.standard.se3.cal import Cal

import matplotlib.pyplot as plt
font = {'family' : 'normal',
        'weight' : 'bold',
        'size'   : 18}
plt.rc('font', **font)

def main():
    io = Io()
    io.eval_args()
    args = sys.argv
    fail = False
    ret = {'ok':True}

    if '--ids' in args:
        idx_ids = args.index('--ids') + 1 
        try:
            ids = args[idx_ids].split('@')
        except:
           fail = True

    if not fail and len(ids) >0:
        for doc_id in ids:
            doc = io.get_doc_db(doc_id)
            T = Temperature(doc, quant='Analysis')
            p = Pressure(doc, quant='Analysis')
            e = Error(doc, quant='Analysis')
            u = Uncertainty(doc, quant='Analysis')

            p_ind, u_p_ind = p.get_value_and_unit('ind_corr')
            p_cal, u_p_cal = p.get_value_and_unit('cal')
            err = p_ind/p_cal -1
            u_err = "1"
            plt.subplot(111)
            x = p_cal
            y = err
            plt.plot(x, y, '.')
            plt.xscale('symlog', linthreshx=1e-12)
            plt.xlabel('pressure in {}'.format(u_p_cal))
            plt.ylabel('error in {}'.format(u_err))

            plt.title('calibration document {}'.format(doc_id))
            for i, v in enumerate(x):
                plt.text(v, y[i], i, rotation=45.)


            plt.grid(True)
            plt.show()

if __name__ == "__main__":
    main()
