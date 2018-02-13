import sys
import copy
import numpy as np
from ..vpy_io import Io
from ..constants import Constants


class GroupNormal(object):
    unit = "mbar"

    def __init__(self, doc, devs):
        io = Io()
        self.log = io.logger(__name__)

        self.Const      = Constants(doc)
        self.Devs       = devs
        self.no_of_devs = len(devs)

    def cal_mean_pressure(self, p_arr, unit):
        """At this stage a simple mean value.

         .. todo:: implement CDG untcertainty, calculate a weighted mean value

        """

        return np.nanmean(p_arr, axis=0)

    def get_error_iterpol(self, p_arr, unit):
        N, M = p_arr.shape
        if self.no_of_devs == N:
            ret = np.full( p_arr.shape, np.nan)
            for i  in range(N):
                pi  = p_arr[i]
                po  = np.full(M, np.nan)

                Dev = self.Devs[i]

                min = Dev.interpol_min
                max = Dev.interpol_max

                j   = np.where(pi > min)
                k   = np.where(pi < max)
                jk  = np.intersect1d(j, k)

                if len(jk) > 0:
                    po[jk] = Dev.get_error_interpol(pi[jk], self.unit)

                ret[i][:] = po[:]
        else:
            self.log.error("Number of Devices dos not match dataset shape")

        return ret
