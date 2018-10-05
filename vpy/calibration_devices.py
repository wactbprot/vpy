import sys
from .document import Document


class CalibrationObject(Document):
    """CalibrationObjects
    """

    def __init__(self, doc):

        if 'State' in doc:
            doc = doc['State']

        if 'Calibration' in doc:
            doc = doc['Calibration']

        if 'CalibrationObject' in doc:
            cob = doc['CalibrationObject']
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
            doc = doc['Calibration']

        if 'CustomerObject' in doc:
            cob = doc['CustomerObject']
            super().__init__(cob)

            if "Class" in cob:
                self.device_class = cob['Class']

    def get_class(self):
        return self.device_class
