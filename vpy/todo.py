import sys
import numpy as np
from .document import Document

class ToDo(Document):
    """Initialisation of ToDo class.

    :param doc: doc ToDo to search and extract
    :type doc: dict
    """

    def __init__(self, doc):

        if 'Calibration' in doc:
            doc = doc['Calibration']

        if 'ToDo' in doc:
            doc = doc['ToDo']

        if 'Pressure' in doc:
            super().__init__(doc['Pressure'])

        self.log.debug("init func: {}".format(__name__))