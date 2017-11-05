from log import log
import numpy as np
from document import Document
from constants import Constants


class Device(Document):
    """ Class should be complete with
    self.Const and self.Dev, nothing more
    """

    log = log().getLogger(__name__)
    log.info("Document class ini")

    def __init__(self, doc, dev):
        super().__init__(dev)
        self.Const = Constants(doc)
