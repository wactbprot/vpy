import sys
from .document import Document
from .vpy_io import Io

class Constants(Document):
    """Initialisation of Constant class.

    .. todo::
        * impl. def get_mol_weight(gas) done
        * impl. def get_visc(gas)

    :param doc: doc constants to search and extract
    :type doc: dict
    """


    io = Io()
    log = io.logger(__name__)
    log.info("start logging")

    def __init__(self, doc):
        if 'Calibration' in doc:
            dc = doc['Calibration']
            if 'Constants' in dc:
                super().__init__(dc['Constants'])

        if 'Constants' in doc:
            super().__init__(doc['Constants'])

    def get_name(self):
        return "Constants"

    def get_mol_weight(self, gas, unit):
        """Returns the molecular weight.

        :param gas: gas (N2, Ar, He ect.)
        :type gas: str

        :param unit: unit (e.g. kg/mol)
        :type unit: str

        :returns: molecular weight
        :rtype: np.array
        """

        if unit is not None:
            if gas is not None:
                return self.get_value( "molWeight_{}".format(gas), unit)
            else:
                errmsg ="no gas given"
                self.log.error(errmsg)
                sys.exit(errmsg)

        else:
            errmsg ="no unit given"
            self.log.error(errmsg)
            sys.exit(errmsg)


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
