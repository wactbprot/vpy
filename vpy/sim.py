import copy
import json

class Sim(object):

    def __init__(self, name):
        self.name = name

    def refresh_base_doc(self, name):
        srv  = couchdb.Server(self.config['db']['url'])
        db   = srv[self.config['db']['name']]
        view = self.config['standards'][name]['temp_doc_view']

        doc = {
                "Standard":{},
                "Constants":{},
                "CalibrationObject":[]
                }

        for item in db.view(view):
            if item.key == "Standard":
                doc["Standard"] = item.value["Standard"]

            if item.key == "Constants":
                doc["Constants"] = item.value["Constants"]

            if item.key == "CalibrationObject":
                doc["CalibrationObject"].append(item.value["CalibrationObject"])

        with open("vpy/standard/{}/base_doc.json".format(name), 'w') as f:
            json.dump(temp_doc, f, indent=4, ensure_ascii=False)

        return temp_doc

    def collect(self,f):
        with open(f) as jf:
            d = json.load(jf)

        o = {}
        for m in d: # Temperature ect.
            o[m] = []
            for n in d[m]: #
                for v in d[m][n]:
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
