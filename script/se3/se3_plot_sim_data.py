import sys
import os
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
    cal.pressure_cal(res)
    cal.error_pressure_rise(res)
    cal.pressure_cal(res)

    uncert = Uncert(doc)
    uncert.define_model()
    uncert.gen_val_dict(res)
    uncert.gen_val_array(res)
    uncert.volume_start(res)
    uncert.volume_5(res)
    uncert.pressure_fill(res)
    uncert.temperature_after(res)
    uncert.temperature_before(res)
    uncert.expansion(res)
    uncert.total_standard(res)
    
    
    p_cal = res.pick("Pressure", "cal", "Pa")
    p_fill = res.pick("Pressure", "fill", "Pa")
    u_1 = res.pick("Uncertainty", "v_start", "1")
    u_2 = res.pick("Uncertainty", "v_5", "1")
    u_3 = res.pick("Uncertainty", "p_fill", "1")
    u_4 = res.pick("Uncertainty", "t_before", "1")
    u_5 = res.pick("Uncertainty", "t_after", "1")
    u_6 = res.pick("Uncertainty", "f", "1")
    u = res.pick("Uncertainty", "standard", "1")
    

    figure(num=None, figsize=(16, 9), dpi=80, facecolor='w', edgecolor='k')

    plt.plot(p_cal, u  , 'H-',lw=3, color=col_map[7], label="total (k=1)" )
    plt.plot(p_cal, u_3, '*-',lw=3, color=col_map[3], label="$p_{fill}$" )
    plt.plot(p_cal, u_6, 's-',lw=3, color=col_map[6], label="$f_i$" )
    plt.plot(p_cal, u_4, 'd-',lw=3, color=col_map[4], label="$T_{before}$" )
    plt.plot(p_cal, u_5, 'v-',lw=3, color=col_map[5], label="$T_{after}$" )
    plt.plot(p_cal, u_1, 'D-',lw=3, color=col_map[1], label="$V_{start}$" )
    plt.plot(p_cal, u_2, 'x-',lw=3, color=col_map[2], label="$V_5$" )


    plt.xscale('symlog', linthreshx=1e-12)
    plt.xlabel('$p_{}$ in {}'.format("{cal}", "Pa"))
    plt.ylabel('$u(p_{cal})$ (relative, k=1)')
    plt.grid(True)
    plt.legend()
    plt.savefig("se3_unert_overview.pdf")
    plt.show()
    startsstr = "CDG_10T_1"

  
    figure(num=None, figsize=(16, 9), dpi=80, facecolor='w', edgecolor='k')

    u_is = res.get_type_array("Uncertainty", starts_with="CDG_10T_1")
    for u_i in u_is:
        u = res.pick("Uncertainty", u_i, "Pa")
        descr = res.pick_dict("Uncertainty", u_i).get("Description").split(",")[0]
        plt.plot(p_cal, u/p_fill, 'x-', lw=3, label="{}: {}".format(u_i, descr ))
             
    plt.xscale('symlog', linthreshx=1e-12)
    plt.xlabel('$p_{}$ in {}'.format("{cal}", "Pa"))
    plt.ylabel('$u(p_{pfill})$ (relative, k=1)')
    #plt.ylim(0, 0.002)
    plt.grid(True)
    plt.legend(ncol=1, fancybox=True, framealpha=0.2)
    plt.savefig("se3_unert_filling_pressure{}.pdf".format(startsstr))
    plt.show()


if __name__ == "__main__":
    main()
