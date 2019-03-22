"""
$> python script/group_normal/frs5_group_normal_se3.py --id cal-2019-frs5-ik-4050_0002 -s
"""
import sys
import os
sys.path.append(os.environ["VIRTUAL_ENV"])


from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.frs5.cal import Cal
from vpy.standard.frs5.uncert import Uncert
from vpy.device.cdg import InfCdg
import numpy as np
import matplotlib.pyplot as plt

def main():

    plt.figure(num=None, figsize=(15, 10), facecolor='w', edgecolor='k')
    markers =("o", "D", "s", ">", "^", "1", "2", "3", "4")
    colors = ('b', 'g', 'r', 'c', 'm', 'y', 'k', 'b', 'g')
    heads = (
        #"1T_1","1T_2","1T_3",
        #"10T_1","10T_2","10T_3",
        "100T_1", "100T_2", "100T_3",
    )
    
    io = Io()
    io.eval_args()
    doc = io.load_doc()

    res = Analysis(doc)
    cal = Cal(doc)
    uncert = Uncert(doc)
    
    p_unit = 'Pa'
    e_unit = '1'
    u_unit = '1'

    cal.temperature(res)

    cal.pressure_res(res)

    cal.pressure_cal(res)
    print("-----------------------------")
    uncert.total_standard(res)
    print("-----------------------------")

    p_conv = cal.Cons.get_conv(cal.unit, p_unit)
    p_cal = res.pick("Pressure", "cal", cal.unit)*p_conv
    ## everything from her runs in p_unit
    u_std = res.pick("Uncertainty", "frs5_total_rel", u_unit)
    m_time = cal.Time.get_value("amt_meas", "ms")
    
    title = doc.get('_id') +heads[0]
    plt.subplot(111)
    for i, head in enumerate(heads):

        device = io.get_doc_db('cob-cdg-se3_{head}'.format(head=head))
        cdg = InfCdg(doc, device)
        p_off = cal.Aux.get_val_by_time(m_time, "offset_mt", "ms", "{head}-ind_offset".format(head=head), p_unit)
        p_ind = cal.Pres.get_value("{}-ind".format(head), p_unit)
        p_ind_corr = p_ind - p_off
      
        plt.semilogx(p_ind_corr, p_ind_corr/p_cal-1, marker = markers[i], markersize=10,  linestyle = 'None', color=colors[i], label = "{head} meas.".format(head=head))
        
        #plt.xlim( (10, 12000) )
        #plt.ylim( (-5e-3, 2e-2) )
        
        plt.legend() 
        
        ## cut values for device
        p_cal_dev = cdg.shape_pressure(p_cal)
        p_cal_dev, l = cdg.rm_nan(p_cal_dev)
        p_ind_corr, _ = cdg.rm_nan(p_ind_corr, l)
        u_std_dev, _ = cdg.rm_nan(u_std, l)
#
        # cal uncertainty
        u_dev = cdg.get_total_uncert(p_ind_corr, p_unit, p_unit)
        u = np.divide(np.sqrt(u_std_dev**2 + u_dev**2), p_cal_dev)
#       # cal error
        e, e_unit = cdg.error(p_cal_dev,  p_ind_corr, p_unit)
           
        # cal interpolation
        p_ind_corr, e, u = cdg.cal_interpol( p_ind_corr, e, u)
        
        res.store("Pressure", "{head}-ind_corr".format(head=head), p_ind_corr, p_unit)
        res.store("Error", "{head}-ind".format(head=head), e, e_unit)
        res.store("Uncertainty", "{head}-total".format(head=head), u, u_unit)
        io.save_doc(res.build_doc())

        # store and save
        cdg.store_interpol(p_ind_corr, e, u, p_unit, e_unit, u_unit)
        io.save_doc(cdg.doc)

        plt.errorbar(p_ind_corr, e, yerr=u, capsize=5, marker = markers[i], linestyle="None", color=colors[i], label = "{head} interp. and uncert.".format(head=head))
        plt.legend()

    for i, head in enumerate(heads):
        # control saved interpolation

        device = io.get_doc_db('cob-cdg-se3_{head}'.format(head=head))
        cdg = InfCdg(doc, device)

        p_ind = cdg.get_value(value_type='p_ind', value_unit=p_unit)
        e = cdg.get_value(value_type='e', value_unit=e_unit)
        
        plt.semilogx(p_ind, e, marker = markers[i], markersize=4,  linestyle = ':', color=colors[i], label="{head} stored".format(head=head))
        plt.legend()

    plt.title(title)
    plt.xlabel(r'$p_{ind} - p_{r}$ in Pa' )
    plt.ylabel(r'$e$ (relative)')
    plt.grid()
    plt.savefig("{title}.pdf".format(title=title))
    plt.show()

if __name__ == "__main__":
    main()
