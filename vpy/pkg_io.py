import logging
import coloredlogs
import argparse
import sys
import os
import json
import couchdb


class Io(object):
    """docstring for Io."""

    def __init__(self):
        """
        Parses the command line argumets.
        Gets the configuration out of the file: *config.json*.
        Provides database
        """

        parser = argparse.ArgumentParser()
        # --id
        parser.add_argument("--id", type=str, nargs=1,
                            help="id of the document to analyse")
        # --id
        parser.add_argument("--db", type=str, nargs=1,
                            help="name of the database")
        # --id
        parser.add_argument("--srv", type=str, nargs=1,
                            help="server url in the form: http://server:port")
        # --file
        parser.add_argument("--file", type=str, nargs=1,
                            help="file containing document to analyse")
        # --log
        parser.add_argument("--log", type=str, nargs=1,
                            help="""kind of logging:
                                      d ... debug
                                      i ... info (default)
                                      e .. error""")
        parser.add_argument('-s', action='store_true',
                            help='save the results of calculation', default=False)

        self.args = parser.parse_args()

        self.log = self.logger(__name__)
        self.log.debug("init func: {}".format(__name__))

        # open and parse config file
        with open('./conf.json') as json_config_file:
            self.config = json.load(json_config_file)

        # save doc
        if self.args.s:
            self.save = True
        else:
            self.save = False

        if self.args.db:
            self.config["db"]["name"] = self.args.db[0]
            self.log.debug("use database {}".format(self.config["db"]["name"]))

        if self.args.srv:
            self.config["db"]["url"] = self.args.srv[0]
            self.log.debug("use server {}".format(self.config["db"]["url"]))

    def load_doc(self):
        """Loads the document to analyse from the source
        given with the command line arguments
        """
        doc = None

        if self.args.id:
            docid = self.args.id[0]
            self.log.info("""try to get document {}
                          from database""".format(docid))
            doc = self.get_doc_db(docid)

        if self.args.file:
            fname = self.args.file[0]
            self.log.info("""try to get document {}
                          from file""".format(fname))
            with open(fname) as json_doc_file:
                doc = json.load(json_doc_file)

        if doc:
            self.log.info("got doc, will return")
            return doc
        else:
            err_msg = "document not found"
            self.log.error(err_msg)
            sys.exit(err_msg)

    def save_doc(self, doc):
        """Saves the document. The location depends on
        command line arguments:

        * *--id*: back do databes
        * *--file*: new.<filename>
        """
        if self.save:
            if self.args.id:
                self.log.info("try writing doc to database")
                doc = self.set_doc_db(doc)

            if self.args.file:
                path_file_name = self.args.file[0]
                path, file_name = os.path.split(path_file_name)
                new_file_name = "{}/new.{}".format(path, file_name)

                self.log.info("""try writing doc to
                            new filename: {}""".format(new_file_name))
                with open(new_file_name, 'w') as f:
                    json.dump(doc, f, indent=4, ensure_ascii=False)
        else:
            self.log.warn("Result is not saved (use -s param)")

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
                self.log.error(err_msg)
                sys.exit(err_msg)
            else:
                self.log.info("""got document from database """)
        else:
            err_msg = """document with id {}
                      not found""".format(doc_id)
            self.log.error(err_msg)
            sys.exit(err_msg)

        return doc

    def set_doc_db(self, doc):
        """ Writes doc back do database.

        :param doc: document
        :type doc: dict
        """
        srv = couchdb.Server(self.config['db']['url'])
        db = srv[self.config['db']['name']]
        res = db.save(doc)

    def update_cal_doc(self, doc, base_doc):
        """More or less a merge between ``doc`` and ``base_doc``.

        :param doc: document containing measurement data
        :type doc: dict

        :param base_doc: document containing data about standard constants CalibrationObjects
        :type base_doc: dict

        :returns: updated calibration document
        :rtype: dict
        """
        ret = None
        if "Calibration" in doc:
            for k, v in base_doc.items():
                doc["Calibration"][k] = v
            ret = doc
        else:
            err_msg = "wrong data structure"
            self.log.error(err_msg)
            sys.exit(err_msg)
        return ret

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

        doc = {
            "Standard": {},
            "Constants": {},
            "CalibrationObject": []
        }
        cob = {}
        val = {}

        for i in db.view(view):
            if i.key == "Standard":
                doc["Standard"] = i.value["Standard"]

            if i.key == "Constants":
                doc["Constants"] = i.value["Constants"]

            if i.key == "CalibrationObject":
                cob[i.value["CalibrationObject"]["Sign"]
                    ] = i.value["CalibrationObject"]

            if i.key.startswith("Result"):
                val[i.value["Sign"]] = i.value["Result"]

        for j in cob:
            if j in val:
                cob[j]["Values"] = val[j]

            doc["CalibrationObject"].append(cob[j])

        return doc

    def get_state_doc(self, name):
        """Gets and returns:

         a) a certain document with ```doc_id``` or
         b) the latest

        containing the additional volume outgasing rate ect.

        :param name: name of the calibration standard
        :type name: str

        :returns: document
        :rtype: dict
        """
        srv = couchdb.Server(self.config['db']['url'])
        db = srv[self.config['db']['name']]

        if self.args.id:
            self.log.info("""try to get document {}
                          from database""".format(self.args.id))
            doc_id = self.args.id[0]
            doc = self.get_doc_db(doc_id)
        else:
            view = self.config['standards'][name]['state_doc_view']
            for item in db.view(view):
                doc = item.value

            self.args.id = doc['_id']

        return doc

    def logger(self, name):
        """
        Based on http://docs.python.org/howto/logging.html#configuring-logging

        .. todo::

                something is wrong here, double output on level=info!

        """

        logger = logging.getLogger()
        fmt = '%(asctime)s,%(msecs)03d %(hostname)s %(filename)s:%(lineno)s %(levelname)s %(message)s'
        if self.args.log:
            if self.args.log[0] == "d":
                coloredlogs.install(fmt=fmt, level="DEBUG", logger=logger)

            if self.args.log[0] == "i":
                coloredlogs.install(fmt=fmt, level="INFO", logger=logger)

            if self.args.log[0] == "e":
                coloredlogs.install(fmt=fmt, level="ERROR", logger=logger)

        else:
            coloredlogs.install(fmt=fmt, level="DEBUG", logger=logger)

        return logger
