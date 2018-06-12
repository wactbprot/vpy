import numpy as np
from ..document import Document
from ..constants import Constants

class Device(Document):
    """ Class should be complete with
    self.Const and self.Dev, nothing more
    """

    def __init__(self, doc, dev):
        self.Const = Constants(doc)

        if "Uncertainty" in dev:
            self.uncert_dict = dev["Uncertainty"]

        super().__init__(dev)


    def get_total_uncert(self, meas, unit, runit):
            """ Collects all Uncertainty contrib for the given
            measurant (m). Calculates the quadratic sum and returns
            a np.array of the length as m.

            .. todo::
                    Test Expression branch
            """
            u_arr = []
            N     = np.shape(meas)[0]
            if "uncert_dict" in self.__dict__:
                u_dict = self.uncert_dict
                for u_i in u_dict:
                    u   = np.full(N, np.nan)
                    idx = np.full(N, True)

                    if "From" in u_i and "To" in u_i and "RangeUnit" in u_i:
                        range_conv = self.Const.get_conv(u_i["RangeUnit"], unit)
                        if u_i["RangeUnit"] and unit == "K":
                            f = float(u_i["From"])+range_conv
                            t = float(u_i["To"])+range_conv
                        else:
                            f = float(u_i["From"])*range_conv
                            t = float(u_i["To"])*range_conv

                        i = (meas > f) & (meas < t)
                        if len(i) > 0:
                            idx = i

                    if "Value" in u_i:
                        u[idx] = float(u_i["Value"])

                    if "Expression" in u_i:
                        # untested
                        fn = sym.lambdify(self.symb, u_i["Expression"], "numpy")
                        u  = fn(*self.val_arr)

                    if "Unit" in u_i:
                        if u_i["Unit"] != "1":
                            conv = self.Const.get_conv(u_i["Unit"], runit)
                            if  unit =="C" and runit == "K":
                                u = u+conv
                            else:
                                u = u*conv
                        else:
                            conv = self.Const.get_conv(unit, runit)
                            if unit =="C" and runit == "K":
                                u = (u+conv)*meas
                            else:
                                u = u*meas*conv

                    u_arr.append(u)

                u = np.sqrt(np.nansum(np.power(u_arr, 2), axis=0))

                idx = (u == 0.0)
                if len(idx) > 0:
                    u[idx] = np.nan

                return u
            else:
                sys.exit("No uncertainty dict available")
