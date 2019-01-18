import numpy as np
import sympy as sym
from ...values import Values, Temperature, Pressure, Date
from .std import Se2
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

class Cal(Se2):

    def __init__(self, doc):
        super().__init__(doc)

        self.Val = Values(doc)
        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Date = Date(doc)
        self.CFaktor = Values(doc['Calibration']['Measurement']['Values']['faktor'])

    def get_expansion(self):
        """Returns an np.array

        :returns: array of expansion names
        :rtype: np.array of strings
        """
        pass

    
    def temperature_after(self, ana):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        T_after_val, T_after_unit = self.Temp.get_value_and_unit("T_after")
        T_after_val = T_after_val + self.Cons.get_conv(T_after_unit, "C")
        ana.store("Temperature", "after", T_after_val, "C")


    def temperature_room(self, ana):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        T_room_val, T_room_unit = self.Temp.get_value_and_unit("T_room")
        T_room_val = T_room_val + self.Cons.get_conv(T_room_unit, "C")
        ana.store("Temperature", "room", T_room_val, "C")
    
    
    def pressure_cal(self, ana):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_cal_val, p_cal_unit = self.Pres.get_value_and_unit("p_cal")
        p_cal_val = p_cal_val * self.Cons.get_conv(p_cal_unit, "mbar")
        ana.store("Pressure", "cal", p_cal_val, "mbar")


    def pressure_ind(self, ana):
        """Simple translation from Measurement to Analysis
           "ind" = "p_cor" != "p_ind"   !!!!

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_cor_val, p_cor_unit = self.Pres.get_value_and_unit("p_cor")
        p_cor_val = p_cor_val * self.Cons.get_conv(p_cor_unit, "mbar")
        ana.store("Pressure", "ind", p_cor_val, "mbar")


    def pressure_offset(self, ana):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_off_val, _ = self.Pres.get_value_and_unit("p_offset")
        cf = self.CFaktor.get_value("faktor","")
        p_off_val = p_off_val * cf

        ana.store("Pressure", "offset", p_off_val, "mbar")


    def pressure_indication_error(self, ana):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_ind = ana.pick("Pressure", "ind", "mbar")
        p_cal = ana.pick("Pressure", "cal", "mbar")
        error = (p_ind - p_cal) / p_cal * 100

        ana.store("Error", "ind", error, "%")


    def measurement_time(self, ana):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        time = self.Date.parse_labview_date()
        ana.store("Date", "measurement", time, "date")


    def reject_outliers_index(self, ana):
        """Reject outliers by several filtering algorithms.
        """

        p_cal = ana.pick("Pressure", "cal", "mbar")
        error = ana.pick("Error", "ind", "%")
        self.ToDo.make_average_index(p_cal, "mbar")
        idx = self.ToDo.average_index

        idx = ana.coarse_error_filtering(average_index=idx)
        idx, ref_mean, ref_std, loops = ana.fine_error_filtering(average_index=idx)

        fig, ax = plt.subplots()
        x = [np.mean(np.take(p_cal, i).tolist()) for i in idx]
        ax.errorbar(x, ref_mean, ref_std, fmt='o', label="ref_mean")
        x = np.take(p_cal, self.Val.flatten(idx)).tolist()
        y = np.take(error, self.Val.flatten(idx)).tolist()
        ax.semilogx(x, y, 'o', label="after refinement!")
        point_label = self.Val.flatten(idx)
        for i in range(len(x)):
            plt.text(x[i], y[i], point_label[i], fontsize=8, horizontalalignment='center', verticalalignment='center')
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels, loc=0)
        plt.title(str(loops) + " mal durchlaufen")
        plt.grid(True, which='both', linestyle='-', linewidth=0.1, color='0.85')
        plt.xlabel(r"$p_\mathrm{cal}$ (mbar)")
        plt.ylabel(r"$e\;(\%)$")
        plt.savefig("reject_outliers_" + str(ana.org["Calibration"]["Certificate"]) + ".pdf")
        plt.clf()

        idx = ana.ask_for_reject(average_index=idx)
        
        ana.average_index = idx


    def make_main_maesurement_index(self, ana):
        """Collects indices of the main measurement in average_index.

        :returns: list of indices
        :rtype: list
        """

        idx = self.Val.flatten(ana.average_index)
        mdate0 = ana.get_object("Type","measurement")["Value"]
        mdate = np.take(mdate0, idx).tolist()
        occurrences = [[i, mdate.count(i)] for i in list(set(mdate))]
        max_occurrence = sorted(occurrences, key=lambda j: j[1])[-1][0]
        idx = [i for i in idx if mdate0[i] == max_occurrence]

        ana.main_maesurement_index = idx


    def make_pressure_range_index(self, ana):
        """Collects indices of measurements with the same conversion factor in r1.
        Collects indices of measurements within the same decade of p_cal in r2.
        Returns the one with smaller standard deviation in the low pressure range.

        :returns: list of lists of indices
        :rtype: list
        """

        cf = self.CFaktor.get_value("faktor","")
        idx = self.Val.flatten(ana.average_index)

        r1 = {}
        for i in idx:
            for j in r1:
                if np.isclose(cf[i], cf[j], rtol=1.e-3) and np.isfinite(cf[j]):
                    r1[j].append(i)
                    break
            else: r1[i] = [i]
        r1 = list(r1.values())

        p_cal = ana.pick("Pressure", "cal", "mbar")
        p_off = ana.pick("Pressure", "offset", "mbar")
        p_cal_log10 = [int(i) for i in np.floor(np.log10(p_cal))]
        r2 = [[j for j in idx if p_cal_log10[j]==i and np.isfinite(cf[j])] for i in sorted(list(set(p_cal_log10)))]
        if len(r2[0]) < 5: r2 = [[*r2[0], *r2[1]], *r2[2:]]
        if len(r2[-1]) < 5: r2 = [*r2[:-2], [*r2[-2], *r2[-1]]]

        print("pressure ranges for offset stability")
        print(r1)
        print(r2)
        print([self.Val.round_to_sig_dig_array(np.take(p_cal, i), 2).tolist() for i in r1])
        print([self.Val.round_to_sig_dig_array(np.take(p_cal, i), 2).tolist() for i in r2])

        if np.std(np.take(p_off, r1[0])) < np.std(np.take(p_off, r2[0])): r = r1
        else: r = r2
        
        ana.pressure_range_index = r

    
    def fit_thermal_transpiration(self, ana):

        cal = ana.pick("Pressure", "cal", "mbar")
        ind = ana.pick("Pressure", "ind", "mbar")
        error = 100 * (ind - cal) / cal

        def model(p, a, b, c, d):
            return d + 3.5 / (a * p**2 + b * p + c * np.sqrt(p) + 1)

        para_val, covariance = curve_fit(model, cal, error, bounds=([0, 0, 0, -np.inf], [np.inf, np.inf, np.inf, np.inf]), maxfev=1000)
        residuals = model(cal, *para_val) - error
        para_unc = np.sqrt(np.diag(covariance))

        viscous_idx = [i for i in range(len(error)) if 0.8 < cal[i] < max(cal)]
        if len(viscous_idx) >= 4 and abs(np.mean(residuals[viscous_idx])) > 0.1:
            #if the deviation is high and there are enough data points in the viscous regime
            #take the mean of the smallest 3 values (excluding the one at highest pressure)
            evis = np.mean(sorted(error[viscous_idx])[0:3])
        else:
            evis = model(100, *para_val)
        
        evis_dict = {"Type": "evis", "Value": evis, "Unit": "%"}

        ana.store_dict(quant="Error", d=evis_dict, dest="AuxValues", plain=True)


    def make_AuxValues_section(self, ana):

        aux = {
            "MainMaesurementIndex": ana.main_maesurement_index,
            "PressureRangeIndex": ana.pressure_range_index,
            "AverageIndex": ana.average_index,
            "AverageIndexFlat": self.Val.flatten(ana.average_index)
            }

        ana.store_dict(quant="AuxValues", d=aux, dest=None, plain=True)