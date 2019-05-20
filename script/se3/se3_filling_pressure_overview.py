import numpy as np
import sys
import os
sys.path.append(os.environ["VIRTUAL_ENV"])

from vpy.pkg_io import Io
from vpy.standard.se3.cal import Cal

from script.se3.se3_cal_filling_pressure import gen_result_dict, get_expansion_uncert_rel, get_fill_pressure_uncert_rel, get_fill_pressures, skip_by_pressure

import matplotlib.pyplot as plt

def main(cal):
    
    N = 100
    target_cals = np.logspace(-2, 3, num=50)
    target_unit = cal.unit
    
    p_fill = []
    p_cal = []
    f_name = []
    u = []
    
    for i, target_cal in enumerate(target_cals):
        target_fill = get_fill_pressures(cal, target_cal, target_unit)
        f_uncert_rel = get_expansion_uncert_rel(cal, target_cal, target_unit)
        fill_uncert_rel = get_fill_pressure_uncert_rel(cal, target_fill, target_unit)
        u_rel = np.sqrt(np.power(fill_uncert_rel,2) + np.power(f_uncert_rel, 2))
        u_rel = skip_by_pressure(cal, target_fill, u_rel, target_unit)

        res_dict = gen_result_dict(target_fill, u_rel, target_unit)
        
        p_cal.append(target_cal)
        p_fill.append(res_dict["Pressure_fill.Value"])
        u.append(res_dict["Uncertainty_cal.Value"])
        f_name.append(res_dict["Expansion.Value"])
    

    plt.subplot(211)
    x = p_cal
    y = p_fill
    plt.plot(x, y, 'o-')
    plt.xscale('symlog', linthreshx=1e-12) 
    plt.yscale('symlog', linthreshx=1e-12)
    plt.xlabel('$p_{}$ in {}'.format("{cal}", target_unit))
    plt.ylabel('$p_{}$ in {}'.format("{fill}", target_unit))
    for i, v in enumerate(x):
        plt.text(x[i], y[i],  "${}$".format(f_name[i]), 
                            horizontalalignment='left',
                            verticalalignment='bottom',
                            rotation=30.
                            )
    plt.grid(True)

    plt.subplot(212)
    x = p_cal
    y = u
    plt.plot(x, y, 'o-')
    plt.xscale('symlog', linthreshx=1e-12)
    plt.xlabel('$p_{}$ in {}'.format("{cal}", target_unit))
    plt.ylabel('$u(p_{cal})$ (relative)')
    for i, v in enumerate(x):
        plt.text(x[i], y[i],  "${}$".format(f_name[i]), 
                            horizontalalignment='left',
                            verticalalignment='bottom',
                            rotation=30.
                            )
    plt.grid(True)
    plt.savefig("filling_pressure_overview.pdf", orientation='landscape', papertype='a4',)
    plt.show()

if __name__ == "__main__":

    io = Io()
    base_doc = io.get_base_doc(name="se3") 
    cal = Cal(base_doc)
    main(cal)