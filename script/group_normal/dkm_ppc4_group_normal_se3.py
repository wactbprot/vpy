"""
python script/group_normal/dkm_ppc4_group_normal_se3.py --id cal-2019-dkm_ppc4-ik-4050_0001 --db vl_db_work -s

"""

from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.dkm_ppc4.cal import Cal
from vpy.standard.dkm_ppc4.uncert import Uncert

from vpy.device.cdg import InfCdg
import numpy as np
import matplotlib.pyplot as plt

def main():

    plt.figure(num=None, figsize=(15, 10), facecolor='w', edgecolor='k')
    markers =("o", "D", "+", ">", "^", "1", "2", "3", "4")
    colors = ('b', 'g', 'r', 'c', 'm', 'y', 'k', 'b', 'g')
    io = Io() 
    io.eval_args()
    doc = io.load_doc()
    p_unit = 'Pa'
    e_unit = '1'
    u_unit = '1'

    res = Analysis(doc)
    cal = Cal(doc)
    uncert = Uncert(doc)

    cal.temperature(res)
    cal.temperature_correction(res)

    cal.pressure_res(res)
    cal.mass_total(res)
    cal.pressure_cal(res)

    uncert.total(res)
    heads = (
            #"100T_1","100T_2","100T_3",
            "1000T_1","1000T_2","1000T_3"
            )
    p_cal = res.pick("Pressure", "dkm_ppc4", p_unit)
    u_std = res.pick("Uncertainty", "dkm_ppc4_total_rel", u_unit)
    m_time = cal.Time.get_value("amt_meas", "ms")

    title = doc.get('_id') + heads[0]
    plt.subplot(111)
    for i, head in enumerate(heads):

        device = io.get_doc_db('cob-cdg-se3_{head}'.format(head=head))
        cdg = InfCdg(doc, device)

        p_off = cal.Aux.get_val_by_time(m_time, "offset_mt", "ms", "{head}-ind_offset".format(head=head), p_unit)
        p_ind = cal.Pres.get_value("{}-ind".format(head), p_unit)
        p_ind_corr = p_ind - p_off
        
        ## caut values for device
        p_cal_dev = cdg.shape_pressure(p_cal)
        p_cal_dev, l = cdg.rm_nan(p_cal_dev)
        p_ind_corr, _ = cdg.rm_nan(p_ind_corr, l)
        u_std_dev, _ = cdg.rm_nan(u_std, l)

        # cal uncertainty
        u_dev = cdg.get_total_uncert(p_ind_corr, p_unit, p_unit)
        u = np.divide(np.sqrt(u_std_dev**2 + u_dev**2), p_cal_dev)

        # cal error
        e, e_unit = cdg.error(p_cal_dev,  p_ind_corr, p_unit)
        
       
        plt.semilogx(p_ind_corr, e, marker = markers[i], markersize=10,  linestyle = 'None', color=colors[i], label = "{head} meas.".format(head=head))
        plt.legend() 
           
        ## cal interpolation
        p_ind_corr, e, u = cdg.cal_interpol( p_ind_corr, e, u)
        
        res.store("Pressure", "{head}-ind_corr".format(head=head), p_ind_corr, p_unit)
        res.store("Error", "{head}-ind".format(head=head), e, e_unit)
        res.store("Uncertainty", "{head}-total".format(head=head), u, u_unit)
        io.save_doc(res.build_doc())
        ## store and save
        cdg.store_interpol(p_ind_corr, e, u, p_unit, e_unit, u_unit)
        if not heads[0] == "100T_1":
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
