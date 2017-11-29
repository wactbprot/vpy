import numpy as np
from ..vpy_io import Io
from ..document import Document
from ..constants import Constants


class Device(Document):
    """ Class should be complete with
    self.Const and self.Dev, nothing more
    """

    def __init__(self, doc, dev):
        super().__init__(dev)
        self.log.debug("init func: {}".format(__name__))
        self.Const = Constants(doc)
