import argparse
import sys
import os
import re
import json
import couchdb
import tempfile

class Io(object):
    """Class Io should handle all the input
    output issues of the pkg.
    """

    def __init__(self, db_url="http://localhost:5984", db_name = "vl_db"):
        """Change the configuration the python way by a
        direct access to io.config....
        """

        self.config = {
            "plot": {"path": "temppath", "make": True},
            "db": {
                "url": db_url ,
                "name": db_name,
                "work_db":"{}_work".format(db_name)
            },
            "standards": {
                "se3": {
                    "all_doc_view": "se3_req/doc",
                    "state_doc_view": "se3_req/state",
                    "hist_data": "se3_req/group_normal_hist",
                    "device_info": "se3_req/group_normal_info",
                    "device_repeat":"se3_req/repeat"
                },
                 "ce3": {
                    "all_doc_view": "ce3_req/doc"
                },
                "se2": {
                    "all_doc_view": "se2_req/doc",
                    "pn_view": "se2_req/pn_by_date"
                },
                "frs5": {
                    "all_doc_view": "frs5_req/doc"
                },
                "dkm_ppc4":{
                    "all_doc_view": "dkm_ppc4_req/doc"
                }
            },
        "all":{
            "log_data_view":"log_data/name-date",
            "cob_by_owner":"hlp/cob_owner"}
        }
        usr = os.environ.get('CAL_USR')
        pwd = os.environ.get('CAL_PWD')

        if usr and pwd:
            self.config["db"]["usr"] = usr
            self.config["db"]["pwd"] = pwd

            self.config["db"]["url"] = db_url.replace('http://','http://{usr}:{pwd}@'.format(usr=usr, pwd=pwd))

        self.make_plot =  self.config["plot"]["make"]

    def eval_args(self):
        """
        Parses the command line argumets.
        Traverse database commandline options to ``self.config``
        """

        parser = argparse.ArgumentParser()
        # --id
        parser.add_argument("--id", type=str, nargs=1,
                            help="id of the document to analyse")
        # --ids
        parser.add_argument("--ids", type=str, nargs=1,
                            help=";-separated ids of the documents to handle")
        # --skip
        parser.add_argument("--skip", action='store_true',
                            help="results are not included in certificate")
        # --db
        parser.add_argument("--db", type=str, nargs=1,
                            help="name of the database")
        # --srv
        parser.add_argument("--srv", type=str, nargs=1,
                            help="server url in the form: http://server:port")
        # --file
        parser.add_argument("--file", type=str, nargs=1,
                            help="file containing document to analyse")
        # -- min_pressure
        parser.add_argument("--min_pressure", type=str, nargs=1,
                            help="minimal pressure for *whatever*-script")
        # -- max_pressure
        parser.add_argument("--max_pressure", type=str, nargs=1,
                            help="maximal pressure for *whatever*-script")
        # -- target_pressure
        parser.add_argument("--target_pressure", type=str, nargs=1,
                            help="target pressure for *whatever*-script")
        # -- pressure_unit
        parser.add_argument("--pressure_unit", type=str, nargs=1,
                            help="pressure unit of the given pressure params")
        # -s save
        parser.add_argument('-s', action='store_true',
                            help='save the results of calculation', default=False)
        # -u update
        parser.add_argument('-u', action='store_true',
                            help='update calibration doc with standard-, constants-, etc- documents', default=False)
        # -a new AuxValues
        parser.add_argument('-a', action='store_true',
                            help='keep Analysis AuxValues section', default=False)
        # -- target_pressure
        parser.add_argument("--point", type=str, nargs=1,
                            help="select a point from a measurement row")
        # -- measure now
        parser.add_argument("-n", action='store_true',
                            help="measure data set now")

        self.args = parser.parse_args()

        ## make args a bit more friendly
        if self.args.s:
            self.save = True
        else:
            self.save = False

        if self.args.db:
            self.config["db"]["name"] = self.args.db[0]

        if self.args.srv:
            if self.config["db"]["usr"] and self.config["db"]["pwd"]:

                self.config["db"]["url"] = self.args.srv[0].replace('http://','http://{usr}:{pwd}@'.format(usr=self.config["db"]["usr"],
                                                                                                           pwd=self.config["db"]["pwd"]))
            else:
                self.config["db"]["url"] = self.args.srv[0]

        if self.args.u:
            self.update = True
        else:
            self.update = False

        if self.args.a:
            self.auxval = True
        else:
            self.auxval = False

        if self.args.ids:
            ids = re.split("[@;,:]", self.args.ids[0])
            if len(ids) == 0:
                self.ids = False
            else:
                self.ids = ids
        else:
            self.ids = False

        if self.args.skip:
            self.skip = True
        else:
            self.skip = False

        if self.args.n:
            self.n = True
        else:
            self.n = False

    def read_json(self, fname):
        with open(fname) as json_doc_file:
            doc = json.load(json_doc_file)
        return doc

    def load_doc(self):
        """Loads the document to analyse from the source
        given with the command line arguments
        """
        doc = None

        if self.args.id:
            docid = self.args.id[0]
            doc = self.get_doc_db(docid)

        if self.args.file:
            doc = self.read_json(self.args.file[0])

        if doc:
            return doc
        else:
            err_msg = "document not found"
            sys.exit(err_msg)

    def save_doc(self, doc):
        """Saves the document if cli param *-s* is on.
        If the cli param *--file* is given
        the docoment is saved to: *new.<filename>*. Otherwise, the
        document is stored by means of *set_doc_db()*
        """
        if self.save:
            if self.args.file:
                path_file_name = self.args.file[0]
                path, file_name = os.path.split(path_file_name)
                new_file_name = "{}/new.{}".format(path, file_name)
                with open(new_file_name, 'w') as f:
                    json.dump(doc, f, indent=4, ensure_ascii=False)
            else:
                doc = self.set_doc_db(doc)

        else:
            print("Result is not saved (use -s param)")

    def get_doc_db(self, doc_id):
        """Gets the document from the database.

        :param doc_id: document id
        :type doc_id: str

        :returns: assembled dictionary
        :rtype: dict
        """

        srv = couchdb.Server(self.config['db']['url'])
        db = srv[self.config['db']['name']]
        doc = db.get(doc_id)

        if doc:
            if "error" in doc:
                err_msg = """database returns
                          with error: {}""".format(doc['error'])
                sys.exit(err_msg)
        else:
            err_msg = """document with id {}
                      not found""".format(doc_id)
            sys.exit(err_msg)

        return doc

    def set_doc_db(self, doc):
        """ Writes doc back do database.

        :param doc: document
        :type doc: dict
        """
        srv = couchdb.Server(self.config['db']['url'])
        db = srv[self.config['db']['name']]

        old_doc = db.get(doc["_id"])
        if old_doc and not 'error' in old_doc:
            doc["_rev"] = old_doc["_rev"]

        return db.save(doc)

    def update_cal_doc(self, doc, base_doc):
        """More or less a merge between ``doc`` and ``base_doc``.

        :param doc: document containing measurement data
        :type doc: dict

        :param base_doc: document containing data about standard constants CalibrationObjects
        :type base_doc: dict

        :returns: updated calibration document
        :rtype: dict
        """

        if 'Calibration' in doc:
            for k, v in base_doc.items():
                doc['Calibration'][k] = v

        else:
            err_msg = "wrong data structure"
            sys.exit(err_msg)

        return doc

    def get_base_doc(self, name):
        """Gets the latest standard related documents from the given
        database and combines it to one document.

        :param name: name of the standard e.g. ``se2`` or ``se3``
        :type doc: str

        :returns: updated calibration document
        :rtype: dict
        """

        srv = couchdb.Server(self.config['db']['url'])
        db = srv[self.config['db']['name']]
        view = self.config['standards'][name]['all_doc_view']

        doc = {"Standard": {},
               "Constants": {},
               "CalibrationObject": [],}
        cob = {}
        val = {}

        for i in db.view(view):
            if i.key == "Standard":
                doc["Standard"] = i.value.get("Standard")

            if i.key == "Constants":
                doc["Constants"] = i.value.get("Constants")

            if i.key == "CalibrationObject":
                cob[i.value["CalibrationObject"]["Sign"]] = i.value.get("CalibrationObject")

            if i.key.startswith("Result") and i.value.get("Result"):
                val[i.value["Sign"]] = i.value.get("Result")

        for j in cob:
            if j in val:
                cob[j]["Values"] = val[j]

            doc["CalibrationObject"].append(cob[j])

        return doc

    def get_state_doc(self, name, enddate=None, startdate="2022-01-01"):
        """Gets and returns the state document
         containing the additional volume outgasing rate ect.
         who is closest and before the date. if no dfate is given
         the last state doc is returned.

        :param meas_date: measurement date in the form yyyy-mm-dd
        :type meas_date: str

        :param std: name of the calibration standard
        :type std: str

        :returns: document
        :rtype: dict
        """
        srv = couchdb.Server(self.config['db']['url'])
        db = srv[self.config['db']['work_db']]
        view = self.config['standards'][name]['state_doc_view']

        if enddate:
            for item in db.view(view, startkey=startdate.replace("-",""), endkey=enddate.replace("-","")):
                doc = item.value
        else:
            for item in db.view(view):
                doc = item.value

        return doc

    def get_pn_by_date(self, std, cert, date):
        """
        Returns the calibration document for a
        check standard (cert: 0.1Torr PN SE2: 0118 or
        10Torr PN SE2: 9911) for the given date (format yyyy-mm-dd)
        and std (SE2, SE3)
        """
        srv = couchdb.Server(self.config['db']['url'])
        db = srv[self.config['db']['name']]
        view = self.config['standards'][std]['pn_view']

        doc = None
        for item in db.view(view, key="{date}_{cert}".format(date=date, cert=cert)):
            doc = item.value

        return doc

    def get_hist_data(self, std):
        """Gets and returns an array containing history data.
        Please use  the view ``se3_req/views/group_normal_hist/`` as a
        template.

        :param std: name of the calibration standard
        :type std: str

        :returns: document
        :rtype: dict
        """
        srv = couchdb.Server(self.config['db']['url'])
        db = srv[self.config['db']['name']]
        dat = {}

        view = self.config['standards'][std]['hist_data']
        for item in db.view(view):

            dat[item.value["IdentString"]] = item.value


        return dat

    def get_log_data(self, task_name, date_from, date_to):
        """Gets and returns an array containing the log data
        produced by a certain task.

        :param task_name: name of the task
        :type task_name: str

        :param date_from: start date in the form 2020-04-22_14-44
        :type date_from: str

        :param date_to: end date in the form 2020-04-22_14-45
        :type date_to: str

        :returns: document
        :rtype: dict
        """
        srv = couchdb.Server(self.config['db']['url'])
        db = srv[self.config['db']['name']]
        dat = []

        start_key = "{}~{}".format(task_name, date_from)
        end_key = "{}~{}".format(task_name, date_to)

        view = self.config['all']['log_data_view']
        for item in db.view(view, startkey=start_key, endkey=end_key):
            dat.append(item.value)

        return dat

    def cob_by_owner(self, owner):
        """Gets and returns an array containing the all
        `cob`s belonging the given  `owner`.

        :param owner: name of owner
        :type task_name: str

        :returns: document
        :rtype: dict
        """
        srv = couchdb.Server(self.config['db']['url'])
        db = srv[self.config['db']['name']]
        dat = []


        view = self.config['all']['cob_by_owner']
        for item in db.view(view, key=owner):
            dat.append(item.value)

        return dat

    def get_device_info(self, std):
        """Gets and returns an array containing info data.

        :param std: name of the calibration standard
        :type std: str

        :returns: document
        :rtype: dict
        """
        srv = couchdb.Server(self.config['db']['url'])
        db = srv[self.config['db']['name']]
        dat = []

        view = self.config['standards'][std]['device_info']
        for item in db.view(view):

            dat.append(item.value)


        return dat

    def get_device_repeat(self, typehead_producer, std="se3"):
        """Gets and returns an array containing
        error of indication and calibration pressure.

        :param std: name of the calibration standard
        :type std: str

        :returns: document
        :rtype: dict
        """
        srv = couchdb.Server(self.config['db']['url'])
        db = srv[self.config['db']['name']]
        dat = []

        view = self.config['standards'][std]['device_repeat']
        for item in db.view(view, key=typehead_producer):
            dat.append(item.value)


        return dat
