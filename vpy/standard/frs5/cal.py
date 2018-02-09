import numpy as np
import sympy as sym

from .std import Frs5
from ...vpy_io import Io

class Cal(Frs5):

    def __init__(self, doc):
        super().__init__(doc)
        doc = copy.deepcopy(orgdoc)

        # measurement values
        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Time = Time(doc)
        self.Aux  = AuxFrs5(doc)

        # residua pressure device
        self.no_of_meas_points = len(self.Time.get_value("amt_frs5_ind", "ms"))

        self.log.debug("init func: {}".format(__name__))

    def pressure_res(self, res):
        """Calculates the residual Pressure from
        SRG-DCR values.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        tem = self.Temp.get_obj("frs5", "C")
        gas = self.Aux.get_gas()
        mt  = self.Time.get_value("amt_frs5_ind", "ms")

        off = self.Aux.get_obj_by_time(mt, "offset_mt", "ms", "frs_res_off", "DCR")
        res_off = self.ResDev.pressure(off, tem, "mbar", gas)

        ind     = self.Pres.get_obj("frs_res_ind", "DCR")
        res_ind = self.ResDev.pressure(ind, tem, "mbar", gas)
        p_res   = res_ind - res_off

        self.log.debug("residial FRS5 pressure is: {}".format(p_res))

        res.store('Pressure',"frs5_res_off", res_off, "mbar")
        res.store('Pressure',"frs5_res_ind", res_ind, "mbar")
        res.store('Pressure',"frs5_res", p_res , "mbar")

    def temperature(self, res):
        """
        Temperature of the balance.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        tem      = self.Temp.get_value("frs5", "C")
        res.store('Temperature',"frs5", tem , "C")


    def pressure_cal(self, res):
        """Calculates the FRS5 calibration pressure from
        lb indication. This is done by means of the standard
        model (see std.define_model)

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """

        self.define_model(res)
        self.gen_val_array(res)

        conv  = self.Cons.get_conv(self.model_unit, self.unit)

        # correction buoyancy
        f_buoyancy  = sym.lambdify(self.symb,self.model_buoyancy , "numpy")
        corr_rho    = f_buoyancy(*self.val_arr)

        # correction temperature
        f_temp    = sym.lambdify(self.symb, self.model_temp, "numpy")
        corr_temp = f_temp(*self.val_arr)

        # conversion lb to Pa
        f_conv = sym.lambdify(self.symb, self.model_conv , "numpy")(*self.val_arr)

        # offset pressure
        r_0 =  sym.lambdify(self.symb, self.model_offset, "numpy")(*self.val_arr)
        p_0 = r_0*f_conv*conv

        # indication
        r = sym.lambdify(self.symb, self.model, "numpy")(*self.val_arr)
        p = r*conv

        res.store("Correction", "buoyancy_frs5", corr_rho, "1")
        res.store("Correction", "temperature_frs5", corr_temp, "1")
        res.store('Pressure', "frs5_off", p_0, self.unit)
        res.store('Pressure', "frs5", p, self.unit)
