import json
import logging
import coloredlogs


class Log(object):

    def __init__(self):
        """
        Provides logging with the level given in  ``config.json``.
        """
        # open and parse config file
        with open('./conf.json') as json_config_file:
            self.config = json.load(json_config_file)

    def logger(self, name):
        """
        Based on http://docs.python.org/howto/logging.html#configuring-logging
        .. todo::
              something is wrong here, double output on level=info!
        """

        logger = logging.getLogger()
        fmt = '%(asctime)s,%(msecs)03d %(hostname)s %(filename)s:%(lineno)s %(levelname)s %(message)s'

        coloredlogs.install(
            fmt=fmt, level=self.config["loglevel"], logger=logger)

        return logger
