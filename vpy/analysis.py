import datetime
import sys
import subprocess
import copy
import numpy as np
from .document import Document
import math

class Analysis(Document):
    """Holds a deep copy of ``document``. Container for storing
    the results of the calculation. 
    """

    def __init__(self, doc, init_dict=None, insert_dict=None, git_hash=True, analysis_type=None, pressure_unit = "Pa",  error_unit ="1"):
        self.pressure_unit =  pressure_unit
        self.error_unit = error_unit

        if init_dict is None:
            init_dict = {
                        "Date": [{
                        "Type": "generated",
                        "Value": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}],
                        "AuxValues":{
                            "AnalysisProgram": "vpy"
                        },
                        "Values": {},
                        }
        if git_hash:
            init_dict['AuxValues']['AnalysisGitHash'] = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode('ascii').strip()

        if analysis_type:
            init_dict['AnalysisType'] = analysis_type
            self.analysis_type = analysis_type
             
        if insert_dict:
            for insert_key in insert_dict:
                init_dict[insert_key] = insert_dict[insert_key]

        super().__init__(init_dict)
        self.org = copy.deepcopy(doc)

    def store(self, quant, val_type, value, unit, sd=None, n=None, dest='Values', descr=None):
        """Stores the result of a calculation in
        the analysis structure under the given quant[ity]. See function ``store_dict()``
        for a more detailed explanation of ``dest`` and ``quant`` params.

        :param quant: quant measurement quantity (Pressure, Temperature ect)
        :type quant: str
        :param val_type: name of value to store
        :type val: str
        :param value: value of type to store
        :type val: np.array
        :param unit: name of unit to store
        :type val: str
        :param sd:  standard deviation of the single values (optional)
        :type sd: np.array
        :param n:  n of the single values (optional)
        :type np: np.array
        :param dest:  destination (default in Values)
        :type str: str
        """

        value = self.make_writable(value)
        append = True

        o = {"Type": val_type, 
             "Value": value, 
             "Unit": unit}
        
        if descr is not None:
            o["Description"] = descr

        if sd is not None:
            o['SdValue'] = self.make_writable(sd)

        if n is not None:
            o['N'] = self.make_writable(n)

        if dest is not None:
            # simply set if new
            if quant not in self.doc[dest]:
                self.doc[dest][quant] = [o]
                append = False
                self.log.info("set values of type {}".format(val_type))

            # search type and replace if existing
            for i, d in enumerate(self.doc[dest][quant]):
                if d.get("Type") == val_type:
                    self.doc[dest][quant][i] = o
                    append = False
                    break
                    self.log.info("replace values of type {}".format(val_type))

            # append if not exist
            if append:    
                self.doc[dest][quant].append(o)
                self.log.info("append values of type {} in {}".format(val_type, quant))
        else:
            # new
            if quant not in self.doc:
                self.doc[quant] = [o]
                append = False
                self.log.info("set values of type {}".format(val_type))

            # replace
            for i, d in enumerate(self.doc[quant]):
                if d.get("Type") == val_type:
                    self.doc[quant][i] = o
                    append = False
                    break
                    self.log.info("replace values of type {}".format(val_type))
            # append
            if append:
                self.doc[quant].append(o)
                self.log.info("append values of type {}".format(val_type))

    def store_dict(self, quant, d, dest='Values', plain=False):
        """ Appends a dict to document under the given destination. 
        Use this function if the dict d has not a ``Type``, ``Value``, 
        ``Unit`` structure. Otherwise use ``store()``.

        The document structure ``self.doc`` afterwards is:

        .. code-block:: javascript

                {'Values':{quant: [d]}, ..} // plain=False
                {'Values':{quant:  d }, ..} // plain=True

        if only ``quant`` and ``d`` is given. If ``dest`` and ``quant`` is given:

        .. code-block:: javascript

                {'dest':{quant: [d] }, ..} // plain=False
                {'dest':{quant:  d  }, ..} // plain=True

        If ``dest`` is given but not ``quant`` (the quantity is provided by the dict key(s)):

        .. code-block:: javascript

                {{dest: [d] }, ..} // plain=False
                {{dest:  d  }, ..} // plain=True


        A possible call signature is:

        .. code-block:: python

               <cls>.store_dict(quant=None, d={SomeIndex:[1,2,3]}, dest='AuxValues')


        :param quant: quant measurement quantity (Pressure, Temperature, ect)
        :type quant: str
        :param d: dictionary to store
        :type d: dict
        :param dest:  destination like Table, AuxValues or Values (default is Values)
        :type str: str
        :param plain:  if True stores dict w/o creating an array
        :type str: bool
        """

        if isinstance(d, dict):
            for e in d:
                d[e] = self.make_writable(d[e])

            if plain:
                if dest is not None and quant is not None:
                    self.doc[dest][quant] = d
                if quant is not None and dest is None:
                    self.doc[quant] = d
                if quant is None and dest is not None:
                    self.doc[dest] = d
            else:
                if dest is not None and quant is not None:
                    if quant not in self.doc[dest]:
                        self.doc[dest][quant] = []

                    if isinstance(self.doc[dest][quant], list):
                        self.doc[dest][quant].append(d)
                    if isinstance(self.doc[dest][quant], dict):
                        self.doc[dest][quant].update(d)
                        
                if dest is None and quant is not None:
                    if quant not in self.doc:
                        self.doc[quant] = []
                    
                    if isinstance(self.doc[quant], list):
                        self.doc[quant].append(d)
                    if isinstance(self.doc[quant], dict):
                        self.doc[quant].update(d)

                    
                if dest is not None and quant is None:
                    if dest not in self.doc:
                        self.doc[dest] = []
                    
                    if isinstance(self.doc[dest], list):
                        self.doc[dest].append(d)
                    if isinstance(self.doc[dest], dict):
                        self.doc[dest].update(d)

        else:
            msg = "given value is not a dictionary"
            self.log.error(msg)
            sys.exit(msg)

    def get_type_array(self, quant, dest='Values', starts_with=None):
        ret = []
        if dest in self.doc:
            if quant in self.doc[dest]:
                doc = self.doc[dest][quant]
                for d in doc:
                    t = d.get('Type')
                    if starts_with:
                        if t.startswith(starts_with):
                            ret.append(t)
                    else:
                        ret.append(t)
            else:
                msg = "{quant} not in {dest}".format(quant=quant, dest=dest)
                self.log.warn(msg)
        else:
            msg = "{dest} not in self.doc".format(dest=dest)
            self.log.warn(msg)
        return ret

    def pick_dict(self, quant, dict_type, dest='Values'):
        """Picks and returns an already calculated value. 
        
        A possible call signature is:

        .. code-block:: python

               <cls>.pick_dict(quant='SomeIndex', dict_type=None, dest='AuxValues')

        :param quant: quant measurement quantity
        :type quant: str
        :param dict_type: value of type to pick
        :type dict_type: str
        :param dict_unit: dict_unit expected
        :type dict_unit: str
        """
        ret = None

        if dict_type is not None and dest in self.doc and quant in self.doc[dest]:
            for d in self.doc[dest][quant]:
                if d['Type'] == dict_type:
                    ret = d
                    break
        if  dict_type is None and dest in self.doc and quant in self.doc[dest]:
            ret = self.doc[dest][quant]
        
        if  dict_type is None and dest is None and quant in self.doc:
            ret = self.doc[quant]
        
        if  dict_type is None and dest in self.doc and quant is None:
            ret = self.doc[dest]
        
        if ret is None:
            msg = "dict with type {} not found".format(dict_type)
            self.log.warn(msg)
        else:
            return ret

    def pick(self, quant, dict_type, dict_unit, dest='Values', with_stats=False):
        """Picks and returns an already calculated value.

        :param quant: quant measurement quantity
        :type quant: str

        :param dict_type: value of type to pick
        :type dict_type: str

        :param dict_unit: dict_unit expected
        :type dict_unit: str
        """
        value_ret = None
        sd_ret = None
        n_ret = None
        
        if dest in self.doc:
            if quant in self.doc[dest]:
                doc = self.doc[dest][quant]
                for d in doc:
                    if d.get('Type') == dict_type:
                        if with_stats:
                            value_ret, sd_ret, n_ret = self.get_value(dict_type, dict_unit, o=d, with_stats=with_stats)
                        else:    
                            value_ret = self.get_value(dict_type, dict_unit, o=d)
            else:
                msg = "{} not in Values".format(quant)
                self.log.warn(msg)
        else:
            msg = "{} not in self.doc".format(dest)            
            self.log.warn(msg)

        if value_ret is None: 
            msg = "dict with type {} not found".format(dict_type)
            self.log.warn(msg)
        
        if with_stats:
            return value_ret, sd_ret, n_ret
        else:
            return value_ret
    
    def make_writable(self, a):
        """ converts array, nd.array etc. to json writable lists.

        """
        self.log.debug("try to make {a} writable".format(a=a))
        if "tolist" in dir(a):
            if isinstance(a, np.float64):
                a = [a]
            else:
                a = a.tolist()
            b = []
            for v in a:  
                if not isinstance(v, str) and (math.isnan(v) or math.isinf(v)):
                    b.append(None)
                else:
                    b.append(v)
            return b
        return a

    def rm_nan(self, x):
        """
         https://stackoverflow.com/questions/11620914/removing-nan-values-from-an-array
        """
        return x[~np.isnan(x)]


    def ask_for_reject(self, average_index):
        """ Asks for points to reject. removes this points from average_index.
        Returns the resulting array of arrays.
        """
        
        reject = self.org.get('Calibration', {}).get('Analysis', {}).get('AuxValues', {}).get('RejectIndex', [])
        
        text = input("Do you want to keep the current set of rejected data points with indices: " + str(reject) + " (type enter if ok)? ")
        if text != "":
            text = input("Type in new list: ").replace("[","").replace("]","").split(",")
            try:
                reject = np.asarray(text, dtype=int).tolist()
            except:
                reject = []
            print("New list is: " + str(reject))

        self.log.debug("average index before manual remove:{}".format(average_index))
        average_index = [[j for j in i if not j in reject] for i in average_index]
        self.log.debug("average index after manual remove:{}".format(average_index))

        return average_index, reject

    def ask_for_reject_offset(self, average_index):
        """ Asks for points to reject. removes this points from average_index.
        Returns the resulting array of arrays.
        """
        
        reject_offset = self.org.get('Calibration', {}).get('Analysis', {}).get('AuxValues', {}).get('RejectIndexOffset', [])
        
        print("offset index before manual remove: " + str(self.flatten(average_index)))
        text = input("Do you want to keep the current set of rejected offset points with indices: " + str(reject_offset) + " (type enter if ok)? ")
        if text != "":
            text = input("Type in new list: ").replace("[","").replace("]","").split(",")
            try:
                reject_offset = np.asarray(text, dtype=int).tolist()
            except:
                reject_offset = []
            print("New list is: " + str(reject_offset))

        return reject_offset        

    def ask_for_skip(self):
        """ Asks for points to skip. Returns the index array. 
        """
        skip = []
        while True:
            r = input("Skip datapoint number: ")
            if r == "":
                break
            skip.append(int(r))

        return skip
    
    def ask_for_head_temperature(self, temperature_head=None):
        """ Asks for the temperature of the Head in C
        (calibration certificate: T_2).  
        """

        q1 = "\n\n\nHead is\n* thermostated at T_2 = {}°C (enter if ok)\n* type T_2 in °C or \n* 0 for no correction: " 
        text = input(q1.format(temperature_head))

        if text == "0":
            return None, None

        if text != "":
            return float(text), "C"

        if text == "":
            return temperature_head, "C"
        
            
    def ask_for_evis(self, e_vis=None, temperature_head=None):
        """ Asks for e_vis.  
        """
        org_calib = self.org.get('Calibration', {})
        org_result = org_calib.get('Result', {})
        org_ana = org_calib.get('Analysis', {})
        
        e_vis = org_result.get('AuxValues', {}).get('Evis', e_vis)
        if e_vis is None:
            e_vis = org_ana.get('AuxValues', {}).get('Evis', 0)
        
        q1 = "\n\n\nEstimate the relative (unit = 1) value for e_vis={} (type enter if ok): "
        text = input(q1.format(e_vis))
        if text != "":
            e_vis = float(text)

        u_vis = org_result.get('AuxValues', {}).get('Uvis')
        if u_vis is None:
            u_vis = org_ana.get('AuxValues', {}).get('Uvis', 2e-3) 

        q2 = "\n\n\nEstimate the uncertainty (unit = 1) u(e_vis)={} (type enter if ok): "
        text = input(q2.format(u_vis))
        if text != "":
            u_vis = float(text)
        
        return e_vis, 1/(e_vis +1), u_vis, "1"


    def flatten(self, l):
        """Flattens a list of lists.

        :param l: list of lists
        :type cal: list

        :returns: a list
        :rtype: list
        """
        return [item for sublist in l for item in sublist]


    def make_pressure_range_index(self, ana, average_index):
        """Collects indices of measurements with the same conversion factor in r1.
        Collects indices of measurements within the same decade of p_cal in r2.
        Returns the one with smaller standard deviation in the low pressure range.

        :returns: list of lists of indices
        :rtype: list
        """

        faktor = ana.pick_dict("Faktor", "faktor").get("Value")
        rn = ana.pick_dict("Range", "range")
        idx = self.flatten(average_index)

        print("->here<-")
        print(rn)

        r1 = {}
        if rn != None:
            rn = rn.get("Value")
            for i in idx:
                for j in r1:
                    if rn[i] == rn[j]:
                        r1[j].append(i)
                        break
                else: r1[i] = [i]
            r1 = list(r1.values())
        else:
            for i in idx:
                for j in r1:
                    if np.isclose(faktor[i], faktor[j], rtol=1.e-3) and np.isfinite(faktor[j]):
                        r1[j].append(i)
                        break
                else: r1[i] = [i]
            r1 = list(r1.values())    
            if len(r1) > 1:
                faktor = faktor / np.max(faktor)
                rangemultiplier = np.full(len(faktor), "nothing")
                for i in range(len(faktor)):
                    if np.isclose(1., faktor[i], rtol=1.e-3): rangemultiplier[i] = "X1"
                    elif np.isclose(0.1, faktor[i], rtol=1.e-3): rangemultiplier[i] = "X0.1"
                    elif np.isclose(0.01, faktor[i], rtol=1.e-3): rangemultiplier[i] = "X0.01"
                ana.store("Range", "ind", rangemultiplier, "1")

        # p_cal = ana.pick("Pressure", "cal", self.pressure_unit)
        # p_off = ana.pick("Pressure", "offset", self.pressure_unit)
        # p_cal_log10 = [int(i) for i in np.floor(np.log10(p_cal))]
        # r2 = [[j for j in idx if p_cal_log10[j]==i and np.isfinite(faktor[j])] for i in sorted(list(set(p_cal_log10)))]
        # if len(r2[0]) < 5: r2 = [[*r2[0], *r2[1]], *r2[2:]]
        # if len(r2[-1]) < 5: r2 = [*r2[:-2], [*r2[-2], *r2[-1]]]

        # if np.std(np.take(p_off, r1[0])) < np.std(np.take(p_off, r2[0])): r = r1
        # else: r = r2
        
        return r1

    def coarse_error_filtering(self, average_index):
        """Removes indices above threshold.
        """
        found_threshold = False
        error_dict = self.pick_dict(quant='Error', dict_type='ind')
        error_unit = error_dict.get('Unit')
        error_value = error_dict.get('Value')
        if error_unit == "%": 
            threshold = 50.0
            found_threshold = True
        if error_unit == "1": 
            threshold = 0.5
            found_threshold = True
        
        if found_threshold:
            self.log.debug("average index before coarse error filtering:{}".format(average_index))
            average_index = [[j for j in i if abs(error_value[j]) < threshold] for i in average_index]
            self.log.debug("average index before coarse error filtering:{}".format(average_index))
        else:
            msg = "No treshold found; see Error(ind) Unit"
            self.log.error(msg)
            sys.exit(msg)

        return average_index

    def fine_error_filtering(self, average_index):
        """Fine filtering.
        Takes the list of indices of measurement points belonging to a
        certain target pressure and rejects outliers by comparing each
        measurement value to the mean value of the neighbors (without the
        point itself).
        remarks: using the standard deviation of the neighbors is unsatisfactory
        because one may end up with a small value by chance. Probably it is
        better to use a threshold that is decreasing with increasing pressure
        values. Another problem is that iterating over empty lists aborts the
        program.

        ..todo::

                function returns empty arrays for 
                ```len(agerage_index) < 3```

        """
        error_dict = self.pick_dict(quant='Error', dict_type='ind')
        error = error_dict.get('Value')
        self.log.debug("average index before fine error filtering: {}".format(average_index))
    
        k = 0
        while True:
            r = []
            ref_mean = [None] * len(average_index) # evtl. np.full()
            ref_std = [None] * len(average_index)
            s = [None] * len(average_index)
            for i in range(len(average_index)):
                s[i] = 1
                if i > 1:
                    s[i] = i
                if i > len(average_index) - 3:
                    s[i] = len(average_index) - 2
                # collect indices of neighbors
                #print("s["+str(i)+"]="+str(s[i]))
                l = average_index[s[i] - 1: s[i] + 2]
                ref_idx = [item for sublist in l for item in sublist] # flatten                
                rr = []
                for j in range(len(average_index[i])):
                    # indices of neighbors only
                    ref_idx0 = [a for a in ref_idx if a != average_index[i][j]]
                    #print(ref_idx0)
                    ref = np.take(error, ref_idx0).tolist()
                    ref_mean[i] = np.mean(ref)
                    ref_std[i] = np.std(ref)
                    #Only accept indices if error[idx[i][j]] deviates either
                    #less than 0.001 or less than 10*sigma from neighbors
                    if abs(ref_mean[i] - error[average_index[i][j]]) < max(0.001, 10 * ref_std[i]):
                        rr.append(average_index[i][j])
                r.append(rr)

            self.log.debug("s: {}".format(s))

            k = k + 1
            if average_index == r:
                break
            average_index = r
            self.log.debug("average index after fine error filtering: {}".format(average_index))
            
        return average_index, ref_mean, ref_std, k
    
    def reduce_by_average_index(self,  value, average_index):
        """Calculates the mean value for each target pressure.
        """
        return np.asarray([np.nanmean(np.take(value, i)) for i in average_index])
    
    def total_uncert(self):
        
        p_cal = self.pick("Pressure", "cal", self.pressure_unit)
        standard_uncert = self.pick("Uncertainty", "standard", self.error_unit)

        p_ind = self.pick("Pressure", "ind_corr", self.pressure_unit)
        device_uncert = self.pick("Uncertainty", "device", "1")
        u_ind_abs = device_uncert*p_ind

        u_rel = p_ind / p_cal * np.sqrt(np.power(u_ind_abs / p_ind, 2) + np.power(standard_uncert, 2))

        self.store("Uncertainty", "total_rel", np.abs(u_rel) , self.error_unit)
        self.store("Uncertainty", "total_abs", np.abs(u_rel*p_cal) , self.pressure_unit)

    def build_doc(self, dest='Analysis', doc=None):
        """Merges the analysis dict to the original doc and returns it.

        :returns: assembled dictionary
        :rtype: dict
        """
        if doc is not None:
            self.org = doc
            
        if "Calibration" in self.org:
            self.org['Calibration'][dest] = self.doc
        elif "State" in self.org:
            self.org['State'][dest] = self.doc
        else:
            self.org[dest] = self.doc

        return self.org
