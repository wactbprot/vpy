import sys
from .log import log
from .document import Document

class CalibrationObject(Document):
    """CalibrationObjects
    """
    log = log().getLogger(__name__)
    log.info("Document class ini")

    def __init__(self, doc):
        if 'Calibration' in doc:
            dc = doc['Calibration']
            if 'CalibrationObject' in dc:
                cob = dc['CalibrationObject']
                super().__init__(cob)

                if isinstance(cob, list):
                    self.cob_by_name = {}
                    for c in self.doc:
                        cob_name = c['Name']
                        self.cob_by_name[cob_name] = c

    def get_by_name(self, name):
        if name in self.cob_by_name:
            return self.cob_by_name[name]
        else:
            errmsg = "Device with name {} not found".format(name)
            self.log.error(errmsg)
            sys.exit(errmsg)


class CustomerObject(Document):
    """Customer Objects
    """

    def __init__(self, doc):
        if 'Calibration' in doc:
            dc = doc['Calibration']
            if 'CustomerObject' in dc:
                cob = dc['CustomerObject']
                super().__init__(cob)

            if "Class" in cob:
                self.device_class = cob['Class']

    def get_class(self):
        return self.device_class
