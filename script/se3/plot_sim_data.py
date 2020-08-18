import sys
import os
import numpy as np
sys.path.append(os.environ["VIRTUAL_ENV"])
from vpy.analysis import Analysis
from vpy.standard.se3.uncert import Uncert
from vpy.standard.se3.cal import Cal
from vpy.pkg_io import Io

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

def main():
    col_map = ['C0', 'C1','C2', 'C3','C4', 'C5','C6', 'C7','C8']
    font = {'family' : 'normal',
        #'weight' : 'bold',
        'size'   : 18}

    plt.rc('font', **font)
    io = Io()
    fname_val = "./vpy/standard/se3/values_sim.json"
    fname_meas_auxval = "./vpy/standard/se3/meas_aux_values.json"
    fname_ana_auxval = "./vpy/standard/se3/ana_aux_values.json"
    base_doc = io.get_base_doc("se3")
    doc = {"Calibration":{
                "Measurement":{},

        }
    }
    doc = io.update_cal_doc(doc, base_doc)

    doc['Calibration']['Measurement']['Values'] = io.read_json(fname_val)
    doc['Calibration']['Measurement']['AuxValues'] = io.read_json(fname_meas_auxval)

    res = Analysis(doc, insert_dict={'AuxValues': io.read_json(fname_ana_auxval)}, analysis_type="expansion")

    cal = Cal(doc)
    cal.pressure_gn_corr(res)
    cal.pressure_gn_mean(res)
    cal.deviation_target_fill(res)
    cal.temperature_before(res)
    cal.temperature_after(res)
    cal.temperature_room(res)
    cal.temperature_gas_expansion(res)
    cal.real_gas_correction(res)
    cal.volume_add(res)
    cal.volume_start(res)
    cal.expansion(res)
    cal.pressure_rise(res)
    cal.correction_delta_height(res)
    cal.correction_f_pressure(res)
    cal.pressure_cal(res)
    cal.error_pressure_rise(res)
    cal.deviation_target_cal(res)

    f_name = cal.get_expansion_name()

    uncert = Uncert(doc)
    p_cal = res.pick("Pressure", "cal", "Pa")
    p_fill = res.pick("Pressure", "fill", "Pa")
    p_rise = res.pick("Pressure", "rise", "Pa")
    f = res.pick("Expansion", "uncorr", "1")

    V_add = res.pick("Volume", "add", "cm^3")
    V_start = res.pick("Volume", "start", "cm^3")
    T_after = res.pick("Temperature", "after", "K")
    T_before = res.pick("Temperature", "before", "K")

    K_0 = res.pick("Correction", "rg", "1")
    K_1 = res.pick("Correction", "delta_heigth", "1")
    K_2 =  res.pick("Correction", "f_p_dependency", "1")
    K = K_0 * K_1 * K_2

    u_c_1 = uncert.contrib_pressure_fill(p_fill, "Pa")
    u_1 = uncert.pressure_fill(u_c_1, "Pa", p_fill, p_rise, f, V_add, V_start, T_after, T_before, K)

    u_c_2 = uncert.contrib_pressure_rise(p_rise, "Pa")
    u_2 = uncert.pressure_rise(u_c_2, "Pa", p_fill, p_rise, f, V_add, V_start, T_after, T_before, K)

    u_c_3 = uncert.contrib_temperature_before(T_before, "K", f_name = f_name)
    u_3 = uncert.temperature_before(u_c_3,"K", p_fill, p_rise, f, V_add, V_start, T_after, T_before, K)

    u_c_4 = uncert.contrib_temperature_after(T_after, "K")
    u_4 = uncert.temperature_after(u_c_4,"K", p_fill, p_rise, f, V_add, V_start, T_after, T_before, K)

    u_c_5 = uncert.contrib_expansion(f, f_name)
    u_5 = uncert.expansion(u_c_5, "1", p_fill, p_rise, f, V_add, V_start, T_after, T_before, K)

    p_0 = np.array([1250.0])
    p_1 = np.array([500.0])
    p_r = np.array([0.0])
    u_c_6 = uncert.contrib_volume_add(p_0, p_1, p_r, "Pa")
    u_6 = uncert.volume_add(u_c_6, "cm^3", p_fill, p_rise, f, V_add, V_start, T_after, T_before, K)


    ## u1 = np.abs(uncert.sens_pressure_fill(*inp)*u_fill_vpy/p_cal)
    ## u2 = np.abs(uncert.sens_pressure_rise(*inp)* u_p_rise/p_cal)
    ## u3 = np.abs(uncert.sens_temperature_after(*inp)*u_T_after[0]/p_cal)
    ## u4 = np.abs(uncert.sens_temperature_before(*inp)*u_T_before_l[0]/p_cal)
    ## u5 = np.abs(uncert.sens_expansion(*inp)*u_f_l/p_cal)
    ## u6 = np.abs(uncert.sens_volume_start(*inp)*u_V_l/p_cal)
    ## u7 = np.abs(uncert.sens_volume_add(*inp)*u_V_add/p_cal)
    ##
    ##
    ##
    ## p_fill = res.pick("Pressure", "fill", "Pa")
    ## u_1 = res.pick("Uncertainty", "v_start", "1")
    ## u_2 = res.pick("Uncertainty", "v_5", "1")
    ## u_3 = res.pick("Uncertainty", "p_fill", "1")
    ## u_4 = res.pick("Uncertainty", "t_before", "1")
    ## u_5 = res.pick("Uncertainty", "t_after", "1")
    ## u_6 = res.pick("Uncertainty", "f", "1")
    ## u = res.pick("Uncertainty", "standard", "1")
    ##
    ##
    ## figure(num=None, figsize=(16, 9), dpi=80, facecolor='w', edgecolor='k')
    ##
    ## plt.plot(p_cal, u  , 'H-',lw=3, color=col_map[7], label="total (k=1)" )
    ## plt.plot(p_cal, u_3, '*-',lw=3, color=col_map[3], label="$p_{fill}$" )
    ## plt.plot(p_cal, u_6, 's-',lw=3, color=col_map[6], label="$f_i$" )
    ## plt.plot(p_cal, u_4, 'd-',lw=3, color=col_map[4], label="$T_{before}$" )
    ## plt.plot(p_cal, u_5, 'v-',lw=3, color=col_map[5], label="$T_{after}$" )
    ## plt.plot(p_cal, u_1, 'D-',lw=3, color=col_map[1], label="$V_{start}$" )
    ## plt.plot(p_cal, u_2, 'x-',lw=3, color=col_map[2], label="$V_5$" )
    ##
    ##
    ## plt.xscale('symlog', linthreshx=1e-12)
    ## plt.xlabel('$p_{}$ in {}'.format("{cal}", "Pa"))
    ## plt.ylabel('$u(p_{cal})$ (relative, k=1)')
    ## plt.grid(True)
    ## plt.legend()
    ## plt.savefig("se3_unert_overview.pdf")
    ## plt.show()
    ## startsstr = "CDG_10T_1"
    ##
    ##
    ## figure(num=None, figsize=(16, 9), dpi=80, facecolor='w', edgecolor='k')
    ##
    ## u_is = res.get_type_array("Uncertainty", starts_with="CDG_10T_1")
    ## for u_i in u_is:
    ##     u = res.pick("Uncertainty", u_i, "Pa")
    ##     descr = res.pick_dict("Uncertainty", u_i).get("Description").split(",")[0]
    ##     plt.plot(p_cal, u/p_fill, 'x-', lw=3, label="{}: {}".format(u_i, descr ))
    ##
    ## plt.xscale('symlog', linthreshx=1e-12)
    ## plt.xlabel('$p_{}$ in {}'.format("{cal}", "Pa"))
    ## plt.ylabel('$u(p_{pfill})$ (relative, k=1)')
    ## #plt.ylim(0, 0.002)
    ## plt.grid(True)
    ## plt.legend(ncol=1, fancybox=True, framealpha=0.2)
    ## plt.savefig("se3_unert_filling_pressure{}.pdf".format(startsstr))
    ## plt.show()


if __name__ == "__main__":
    main()
