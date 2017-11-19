import logging
import logging.config
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
        ## --id
        parser.add_argument("--id", type = str, nargs = 1,
                            help = "id of the document to analyse")
        ## --file
        parser.add_argument("--file", type = str, nargs = 1,
                            help = "file containing document to analyse")
        ## --log
        parser.add_argument("--log", type = str, nargs = 1,
                            help = """kind of logging:
                                      d ... debug
                                      i ... info (default)
                                      e .. error""")
        parser.add_argument('-s', action='store_true'
                            , help='save the results of calculation'
                            , default=False)

        self.args =  parser.parse_args()
        self.log  = self.logger(__name__)

        if self.args.file:
            ## open and parse config file
            with open('./conf.json') as json_config_file:
                self.config = json.load(json_config_file)

        if self.args.id:
            ## provide data base
            srv     = couchdb.Server(self.config['db']['url'])
            self.db = srv[self.config['db']['name']]

        # save doc

        if self.args.s:
            self.log.info("Will save results")
            self.save = True
        else:
            self.log.info("Will not save results")
            self.save = False



    def load_doc(self):
        """Loads the document to analyse from the source
        given with the command line arguments
        """
        doc = None

        if self.args.id:
            self.log.info("""try to get document {}
                          from database""".format(self.args.id))
            docid = self.args.id[0]
            doc   = self.get_doc_db(docid)

        if self.args.file:
            self.log.info("""try to get document {}
                          from file""".format(self.args.file))
            with open(self.args.file[0]) as json_doc_file:
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
                path_file_name  = self.args.file[0]
                path, file_name = os.path.split(path_file_name)
                new_file_name   = "{}/new.{}".format(path, file_name)

                self.log.info("""try writing doc to
                            new filename: {}""".format(new_file_name))
                with open(new_file_name, 'w') as f:
                    json.dump(doc, f, indent=4, ensure_ascii=False)
        else:
            self.log.warn("Result is not saved (use -s param)")


    def get_doc_db(self, docid):
        """Gets the document from the database.

        :param docid: document id
        :type docid: str
        """
        doc = self.db.get(docid)

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
                      not found""".format(docid)
            self.log.error(err_msg)
            sys.exit(err_msg)

        return doc

    def set_doc_db(self, doc):
        """ Writes doc back do database.

        :param doc: document
        :type doc: dict
        """
        res = self.db.save(doc)


    def logger(self, name):
        """
        Based on http://docs.python.org/howto/logging.html#configuring-logging

        .. todo::

                something is wrong here, double output on level=info!

        """

        logging.config.dictConfig({
            'version': 1,
            'formatters': {
                'default': {'format': '%(asctime)s - %(name)s -[%(filename)s:%(lineno)s - %(funcName)10s() ] - %(levelname)s - %(message)s',
                 'datefmt': '%Y-%m-%d %H:%M:%S'}
            },
            'handlers': {
                'default': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'default',

                },
            },
            'loggers': {
                'default': {
                    'handlers': ['default',
                                ]
                }
            },
            'disable_existing_loggers': False
        })
        logger = logging.getLogger('default')

        if self.args.log:
            if self.args.log[0] == "d":
                logger.setLevel(logging.DEBUG)
                coloredlogs.install(level='DEBUG', logger=logger)

            if self.args.log[0] == "e":
                logger.setLevel(logging.ERROR)
                coloredlogs.install(level='ERROR', logger=logger)

            if self.args.log[0] == "i":
                logger.setLevel(logging.INFO)
                coloredlogs.install(level='INFO', logger=logger)


        return logger
