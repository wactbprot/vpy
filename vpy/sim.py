import copy
import json

class Sim(object):

    def __init__(self, name):
        self.name = name

    def collect(self,f):
        with open(f) as jf:
            d = json.load(jf)

        o = {}
        for m in d: #m ... Temperature ect.
            o[m] = []
            for n in d[m]: # n... 100TFill
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

    def build(self):

        with open('./vpy/standard/{}/base_doc.json'.format(self.name)) as jf:
            self.doc = json.load(jf)

        valfile    = "./vpy/standard/{}/values.json".format(self.name)
        auxvalfile = "./vpy/standard/{}/aux_values.json".format(self.name)

        self.doc['Values']    = self.collect(valfile)
        self.doc['AuxValues'] = self.collect(auxvalfile)

        return copy.deepcopy(self.doc)

if __name__ == "__main__":
    build()
