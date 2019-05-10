import datetime
import sys
import subprocess
import copy
import numpy as np
from .document import Document
import math

class Analysis(Document):
    """Holds a deep copy of ``document``. Container for storing
    the calculation results of analysis.
    """

    def __init__(self, doc, init_dict=None, insert_dict=None, git_hash=True):

        if init_dict is None:
            d = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            init_dict = {
                        "Date": [{
                        "Type": "generated",
                        "Value": d}],
                        "AuxValues":{
                            "AnalysisProgram": "vpy"
                        },
                        "Values": {},
                        }
        if git_hash:
            init_dict['AnalysisGitHash'] = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode('ascii').strip()
        
        

        if insert_dict:
            for insert_key in insert_dict:
                init_dict[insert_key] = insert_dict[insert_key]

        super().__init__(init_dict)
        self.org = copy.deepcopy(doc)

    def store(self, quant, type, value, unit, sd=None, n=None, dest='Values'):
        """Stores the result of a calculation in
        the analysis structure under the given quant[ity]. See function ``store_dict()``
        for a more detailed explanation of ``dest`` and ``quant`` params.

        :param quant: quant measurement quantity (Pressure, Temperature ect)
        :type quant: str
        :param type: name of type to store
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

        o = {"Type": type, "Value": value, "Unit": unit}
        if sd is not None:
            o['SdValue'] = self.make_writable(sd)

        if n is not None:
            o['N'] = self.make_writable(n)

        if dest is not None:
            if quant not in self.doc[dest]:
                self.doc[dest][quant] = []

            self.doc[dest][quant].append(o)
            self.log.info("stored values of type {} in {}".format(type, quant))
        else:
            if quant not in self.doc:
                self.doc[quant] = []
            self.doc[quant].append(o)
            self.log.info("stored values of type {}".format(type))

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
                    self.doc[dest][quant].append(d)
                if dest is None and quant is not None:
                    if quant not in self.doc:
                        self.doc[quant] = []
                    self.doc[quant].append(d)
                if dest is not None and quant is None:
                    if dest not in self.doc:
                        self.doc[dest] = []
                    self.doc[dest].append(d)
        else:
            msg = "given value is not a dictionary"
            self.log.error(msg)
            sys.exit(msg)

   
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
                self.log.error(msg)
                sys.exit(msg)
        else:
            msg = "{} not in self.doc".format(dest)            
            self.log.warn(msg)

        if value_ret is None: 
            msg = "dict with type {} not found".format(dict_type)
            self.log.warn(msg)
        else:
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
                if not isinstance(v, str) and math.isnan(v):
                    b.append(None)
                else:
                    b.append(v)
            return b
        return a
    
    def ask_for_reject(self, average_index):
        """ Asks for points to reject. removes this points from average_index.
        Returns the resulting array of arrays.
        """
        reject = []
        while True:
            r = input("Reject datapoint number: ")
            if r == "":
                break
            reject.append(r)
        self.log.debug("average index before manual remove:{}".format(average_index))
        average_index = [[j for j in i if not str(j) in reject] for i in average_index]
        self.log.debug("average index after manual remove:{}".format(average_index))

        return average_index
    
    def ask_for_evis(self):
        """ Asks for e_vis
        """
        e_vis = 0
        while True:
            r = input("estimate the relativ (unit = 1) value for e_vis={} (empty if ok): ".format(e_vis))
            if r == "":
                break
            e_vis = float(r)

        u_vis = 2e-3
        while True:
            r = input("estimate the uncertainty (unit = 1) u(e_vis)={} (empty if ok): ".format(u_vis))
            if r == "":
                break
            e_vis = float(r)
        return e_vis, 1/(e_vis +1), u_vis, "1"

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
            average_index = [[j for j in i if abs(error_value[j]) < 50] for i in average_index]
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
                l = average_index[s[i] - 1: s[i] + 1]
                ref_idx = [item for sublist in l for item in sublist] # flatten
                rr = []
                for j in range(len(average_index[i])):
                    # indices of neighbors only
                    ref_idx0 = [a for a in ref_idx if a != average_index[i][j]]
                    ref = np.take(error, ref_idx0).tolist()
                    ref_mean[i] = np.mean(ref)
                    ref_std[i] = np.std(ref)
                    #Only accept indices if error[idx[i][j]] deviates either 
                    #less than 5% or 5*sigma from neighbors
                    if abs(ref_mean[i] - error[average_index[i][j]]) < max(5, 5 * ref_std[i]):
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
        return np.asarray([np.mean(np.take(value, i)) for i in average_index])

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
