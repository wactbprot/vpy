import sys
from .log import log
from .document import Document


class Constants(Document):

    log = log().getLogger(__name__)
    log.info("Document class ini")

    def __init__(self, doc):
        """Initialisation of Constant class.

        :param doc: doc constants to search and extract
        :type doc: dict
        """

        if 'Calibration' in doc:
            dc = doc['Calibration']
            if 'Constants' in dc:
                super().__init__(dc['Constants'])

        if 'Constants' in doc:
            super().__init__(doc['Constants'])

    def get_name(self):
        return "Constants"

    def get_conv(self, f, t):
        """Get the conversion factor from unit f to unit t.
        """
        cstr = "{}_2_{}".format(f, t)
        ustr = "{}/{}".format(t, f)
        conv = self.get_value(cstr, ustr)
        if conv is not None:
            self.log.info("search: "+cstr+" in "+ustr+" found: {}".format(conv))
            return conv
        else:
            errmsg = "no conversion factor from {} to {}".format(f, t)
            self.log.error(errmsg)
            sys.exit(errmsg)
