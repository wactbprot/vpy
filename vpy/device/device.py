import numpy as np
from ..vpy_io import Io
from ..document import Document
from ..constants import Constants


class Device(Document):
    """ Class should be complete with
    self.Const and self.Dev, nothing more
    """

    def __init__(self, doc, dev):
        self.log = Io().logger(__name__)
        self.log.info("start logging")
        super().__init__(dev)
        self.Const = Constants(doc)
