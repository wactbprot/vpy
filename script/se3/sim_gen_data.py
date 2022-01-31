import sys
sys.path.append(".")

import os
import json
import numpy as np

from vpy.pkg_io import Io
from vpy.standard.se3.cal import Cal
from script.se3.cal_filling_pressure import gen_result_dict, get_expansion_uncert_rel, get_fill_pressure_uncert_rel, get_fill_pressures, skip_by_pressure

"""
renew data **struct**:
python script/se3/gen_sim_data.py --id 'cal-2019-se3-kk-75051_0001'

generate sim **data**:
python script/se3/gen_sim_data.py
"""

def main(io, cal, config):
    io.eval_args()
    args = sys.argv

    if '--id' in args:
        id = args[args.index('--id') + 1]
        try:
            doc = io.get_doc_db(id)
            val_dict = doc.get("Calibration", {}).get("Measurement", {}).get("Values", {})
            gen_sim_value_struct(val_dict)
        except:
           sys.exit("failed to build structure from: {}".format(id))

    gen_sim_data(cal, config )
    #gen_sim_data(cal, target_pressures= list( np.logspace(-2, 2, num=80)))

def gen_sim_value_struct(val_dict, out_file_name="values_struct.json", path="vpy/standard/se3"):
    res_dict = {}
    for quant in val_dict:

        if quant not in res_dict:
            res_dict[quant] = []

        for d in val_dict[quant]:
           res_dict[quant].append({"Type":d.get("Type"), "Unit":d.get("Unit")})

    with open("{}/{}".format(path, out_file_name), 'w') as f:
        json.dump(res_dict, f, indent=4, ensure_ascii=False)

def get_fill_and_expansion(cal, target_pressures, target_unit):

    expansion_name_value = []
    target_fill_value = []

    for i, target_pressure in enumerate(target_pressures):
        print(target_pressure)
        p_fill = get_fill_pressures(cal, target_pressure, target_unit)
        u_f = get_expansion_uncert_rel(cal, target_pressure, target_unit)
        u_p_fill = get_fill_pressure_uncert_rel(cal, p_fill, target_unit)
        u_rel = np.sqrt(np.power(u_p_fill, 2) + np.power(u_f/3, 2))
        print(p_fill)
        print(u_f)
        print(u_p_fill)
        #u_rel = u_p_fill
        print(np.sqrt(np.power(u_p_fill, 2) + np.power(u_f, 2)))
        #u_rel = u_p_fill
        u_rel = skip_by_pressure(cal, p_fill, u_rel, target_unit)

        res_dict = gen_result_dict(p_fill, u_rel, target_unit)
        expansion_name_value.append(res_dict.get("Expansion").get("Value"))
        target_fill_value.append(res_dict.get("Pressure_fill").get("Value"))

    return target_fill_value, expansion_name_value

def sim_temperature_before(struct_dict, target_fill, target_unit):
    c_type = struct_dict.get("Type")
    c_unit = struct_dict.get("Unit")

    if c_unit == target_unit:
        if c_type.startswith("1T"):
            pass
            # etc. impl sim data here
        T = [23.1 for p_i in target_fill]
    else:
        sys.exit("impl. unit conversion")

    return T

def sim_fill_pressure(struct_dict, target_fill, target_unit):
    c_unit = struct_dict.get("Unit")
    if c_unit == target_unit:
        p = [p_i  for p_i in target_fill]
    else:
        sys.exit("impl. unit conversion")

    return p

def sim_fill_offset(struct_dict, target_fill, target_unit):
    c_unit = struct_dict.get("Unit")

    if c_unit == target_unit:
        p = [0.0  for p_i in target_fill]
    else:
        sys.exit("impl. unit conversion")

    return p

def sim_ind_pressure(struct_dict, target_pressures, target_unit, ind_abs_dev=0, ind_rel_dev=1e-3):
    c_unit = struct_dict.get("Unit")

    if c_unit == target_unit:
        p = [(p_i + ind_abs_dev)*(1 + ind_rel_dev)  for p_i in target_pressures]
    else:
        sys.exit("impl. unit conversion")

    return p

def sim_ind_offset(struct_dict, target_pressures, target_unit, ind_offset_abs_std=1e-5):
    c_unit = struct_dict.get("Unit")

    if c_unit == target_unit:
        p = list(np.random.normal(0, ind_offset_abs_std, len(target_pressures)))
    else:
        sys.exit("impl. unit conversion")

    return p

def sim_temperature_after(struct_dict, target_fill, target_unit):
    c_unit = struct_dict.get("Unit")

    if c_unit == target_unit:
        T = [23.0  for p_i in target_fill]
    else:
        sys.exit("impl. unit conversion")

    return T

def sim_position(struct_dict, target_fill):
    pos = ["open"  for p_i in target_fill]

    return pos

def sim_time(struct_dict, target_fill, meas_time_ms=20000.0):
    c_type = struct_dict.get("Type")

    if c_type == "amt_fill":
        t = [100000*i + 0.0  for i, p in enumerate(target_fill)]
    if c_type == "amt_expansion_start":
        t = [100000*i + 0.0  for i, p in enumerate(target_fill)]
    if c_type == "amt_expansion_end":
        t = [100000*i + meas_time_ms  for i, p in enumerate(target_fill)]

    return t

def gen_sim_data(cal, config):

    target_pressures = config.get("target_pressures")
    struct_path = config.get("struct_path")
    struct_file = config.get("struct_file")
    target_unit = config.get("target_unit")
    values_file = config.get("values_file")

    with open("{}/{}".format(struct_path, struct_file)) as f:
        val_dict = json.load(f)

    target_fill, exp_name = get_fill_and_expansion(cal, target_pressures, target_unit)
    for quant in val_dict:
        for d in val_dict[quant]:
            c_type = d.get("Type")
            c_unit = d.get("Unit")

            if quant == "Pressure" and c_type == "target_pressure":
                d["Value"] = target_pressures

            if quant == "Pressure" and c_type == "target_fill":
                d["Value"] = target_fill

            if quant == "Pressure" and c_type == "ind":
                d["Value"] = sim_ind_pressure(d, target_pressures, target_unit,
                                              ind_abs_dev = config.get("ind_abs_dev"),
                                              ind_rel_dev = config.get("ind_rel_dev"))

            if quant == "Pressure" and c_type == "ind_offset":
                d["Value"] = sim_ind_offset(d, target_pressures, target_unit,
                                            ind_offset_abs_std=config.get("ind_offset_abs_std"))

            if quant == "Expansion" and c_type == "name":
                d["Value"] = exp_name

            if quant == "Pressure" and c_type.endswith("-fill"):
               d["Value"] = sim_fill_pressure(d, target_fill, target_unit)

            if quant == "Pressure" and c_type.endswith("-offset"):
               d["Value"] = sim_fill_offset(d, target_fill, target_unit)

            if quant == "Temperature" and c_type.endswith("_before"):
               d["Value"] = sim_temperature_before(d, target_fill, target_unit="C")

            if quant == "Temperature" and c_type.endswith("_after"):
               d["Value"] = sim_temperature_after(d, target_fill, target_unit="C")

            if quant == "Position":
               d["Value"] = sim_position(d, target_fill)

            if quant == "Time":
               d["Value"] = sim_time(d, target_fill,
                                     meas_time_ms=config.get("meas_time_ms"))


    with open("{}/{}".format(struct_path, values_file), 'w') as f:
        json.dump(val_dict, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    with open('./script/se3/sim_config.json') as f:
        config = json.load(f)

    io = Io()
    base_doc = io.get_base_doc(name="se3")
    cal = Cal(base_doc)
    main(io, cal, config)
