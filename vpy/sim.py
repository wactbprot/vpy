import copy
import json


class Sim(object):

    def __init__(self, name):
        self.name = name

    def collect(self, d):
        
        o = {}
        for m in d:  # m ... Temperature ect.
            o[m] = []

            if isinstance(d[m], str):  # z.B Gas:N2
                o[m] = d[m]
            else:
                for n in d[m]:  # n... 100TFill
                    if isinstance(d[m][n], list):
                        for v in d[m][n]:
                            e = {}
                            if "Type" in v:
                                e["Type"] = v["Type"]

                            if "Sim" in v:
                                e["Value"] = v["Sim"]

                            if "Unit" in v:
                                e["Unit"] = v["Unit"]

                            o[m].append(e)

                    if isinstance(d[m][n], dict):
                        v = d[m][n]

                        e = {}
                        if "Type" in v:
                            e["Type"] = v["Type"]

                        if "Sim" in v:
                            e["Value"] = v["Sim"]

                        if "Unit" in v:
                            e["Unit"] = v["Unit"]

                        o[m].append(e)

        return o

    def get_json(self, fname):

        with open(fname) as jf:
            return json.load(jf)

    def build(self):

        fname_base_doc = './vpy/standard/{}/base_doc.json'.format(self.name)
        fname_val = "./vpy/standard/{}/values.json".format(self.name)
        fname_auxval = "./vpy/standard/{}/aux_values.json".format(self.name)

        doc = self.get_json(fname_base_doc)
        doc['Values'] = self.collect(self.get_json(fname_val))
        doc['AuxValues'] = self.collect(self.get_json(fname_auxval))

        return {"Calibration": doc}


if __name__ == "__main__":
    build()
