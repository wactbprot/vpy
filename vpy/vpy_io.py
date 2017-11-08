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
        self.logger = self.log(__name__)
        parser = argparse.ArgumentParser()
        ## --id
        parser.add_argument("--id", type = str, nargs = 1,
                            help = "id of the document to analyse")

        ## --file
        parser.add_argument("--file", type = str, nargs = 1,
                            help = "file containing document to analyse")

        parser.add_argument('-s', action='store_true'
                            , help='save the results of calculation'
                            , default=False)

        self.args = parser.parse_args()

        ## open and parse config file
        with open('./conf.json') as json_config_file:
            self.config = json.load(json_config_file)

        ## provide data base
        srv     = couchdb.Server(self.config['db']['url'])
        self.db = srv[self.config['db']['name']]

        # save doc

        if self.args.s:
            self.logger.info("Will save results")
            self.save = True
        else:
            self.logger.info("Will not save results")
            self.save = False

    def load_doc(self):
        """Loads the document to analyse from the source
        given with the command line arguments
        """
        doc = None

        if self.args.id:
            self.logger.info("""try to get document {}
                          from database""".format(self.args.id))
            docid = self.args.id[0]
            doc   = self.get_doc_db(docid)

        if self.args.file:
            self.logger.info("""try to get document {}
                          from file""".format(self.args.file))
            with open(self.args.file[0]) as json_doc_file:
                doc = json.load(json_doc_file)

        if doc:
            self.logger.info("got doc, will return")
            return doc
        else:
            err_msg = "document not found"
            self.logger.error(err_msg)
            sys.exit(err_msg)

    def save_doc(self, doc):
        """Saves the document. The location depends on
        command line arguments:

        * *--id*: back do databes
        * *--file*: new.<filename>
        """
        if self.save:
            if self.args.id:
                self.logger.info("try writing doc to database")
                doc = self.set_doc_db(doc)

            if self.args.file:
                path_file_name  = self.args.file[0]
                path, file_name = os.path.split(path_file_name)
                new_file_name   = "{}/new.{}".format(path, file_name)

                self.logger.info("""try writing doc to
                            new filename: {}""".format(new_file_name))
                with open(new_file_name, 'w') as f:
                    json.dump(doc, f, indent=4, ensure_ascii=False)
        else:
            self.logger.warn("Result is not saved (use -s param)")


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
                self.logger.error(err_msg)
                sys.exit(err_msg)
            else:
                self.logger.info("""got document from database """)
        else:
            err_msg = """document with id {}
                      not found""".format(docid)
            self.logger.error(err_msg)
            sys.exit(err_msg)

        return doc

    def set_doc_db(self, doc):
        """ Writes doc back do database.
        :param doc: document
        :type doc: dict
        """
        res = self.db.save(doc)


    def log(self, name):
        """
        Based on http://docs.python.org/howto/logging.html#configuring-logging
        """

        logging.config.dictConfig({
            'version': 1,
            'formatters': {
                'default': {'format': '%(asctime)s - %(name)s -[%(filename)s:%(lineno)s - %(funcName)10s() ] - %(levelname)s - %(message)s',
                 'datefmt': '%Y-%m-%d %H:%M:%S'}
            },
            'handlers': {
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'default',
                    'stream': 'ext://sys.stdout'
                },
                #'file': {
                #    'level': 'DEBUG',
                #    'class': 'logging.handlers.RotatingFileHandler',
                #    'formatter': 'default',
                #    'filename': log_path,
                #    'maxBytes': 1024,
                #    'backupCount': 3
                #}
            },
            'loggers': {
                'default': {
                    'level': 'DEBUG',
                    'handlers': ['console',
                                #'file',
                                ]
                }
            },
            'disable_existing_loggers': False
        })
        coloredlogs.install()

        return logging.getLogger('default')
