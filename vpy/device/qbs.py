import numpy as np
import sympy as sym
from ..device.device import Device
from ..constants import Constants

class Qbs(Device):
    unit = "Pa"

    def __init__(self, doc, dev):
        self.Const = Constants(doc)

        if 'CalibrationObject' in dev:
            dev = dev.get('CalibrationObject')

        super().__init__(doc, dev)

        if 'Interpol' in dev:
            # pressure
            v, u = self.get_value_and_unit('p_ind')
            conv = self.Const.get_conv(from_unit=u, to_unit=self.unit)
            self.interpol_p = v * conv
            # error
            self.interpol_e = self.get_value(value_type='e', value_unit='1')

            interpol_min = np.min(self.interpol_p)
            interpol_max = np.max(self.interpol_p)

            if self.min_p > interpol_min:
                self.interpol_min = self.min_p
            else:
                self.interpol_min = interpol_min
            if self.max_p > interpol_max:
                self.interpol_max =  interpol_max
            else:
                self.interpol_max =  self.max_p

        dev_setup = dev.get('Setup')
        if dev_setup:
            use_from = dev_setup.get('UseFrom')
            use_to = dev_setup.get('UseTo')
            use_unit = dev_setup.get('UseUnit')

        if use_from and use_to and use_unit:
            conv = self.Const.get_conv(from_unit=use_unit, to_unit=self.unit)
            self.max_p = float(use_to) * conv
            self.min_p = float(use_from) * conv



    def get_name(self):
        return self.doc['Name']

    def get_error_correction(self, p, punit, runit):
        """Calculates the error of indication by means of the expression stored

        :param p: p pressure to calculate the error
        :type p: np.array
        :param punit: punit pressure unit
        :type punit: str
        :param runit: runit unit of values returned
        :type runit: str
        """

        e_expr = self.get_expression("e", "%")
        f = sym.lambdify(sym.Symbol('p'), e_expr, "numpy")
        return f(p)
