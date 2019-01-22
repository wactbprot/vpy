import json
import logging
import coloredlogs


class Log(object):

    def __init__(self):
        """
        Provides logging with the level given in  ``config.json``.
        """
        self.level = 'DEBUG'

    def logger(self, name):
        """
        Based on http://docs.python.org/howto/logging.html#configuring-logging

        .. todo::
              something is wrong here, double output on level=info!
        """

        logger = logging.getLogger()
        fmt = '%(asctime)s,%(msecs)03d %(hostname)s %(filename)s:%(lineno)s %(levelname)s %(message)s'

        coloredlogs.install(fmt=fmt, level=self.level, logger=logger)

        return logger
