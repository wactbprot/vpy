import sys
from .document import Document
from .vpy_io import Io

class Constants(Document):
    """Initialisation of Constant class.

    .. todo::
        * impl. def get_mol_weight(gas) done
        * impl. def get_visc(gas)
        * impl. def get_gas_density(gas) -- calculation f(T, gas, p)


    :param doc: doc constants to search and extract
    :type doc: dict
    """

    def __init__(self, doc):

        io = Io()
        self.log = io.logger(__name__)
        self.log.debug("init func: {}".format(__name__))

        if 'Calibration' in doc:
            dc = doc['Calibration']
            if 'Constants' in dc:
                super().__init__(dc['Constants'])

        if 'Constants' in doc:
            super().__init__(doc['Constants'])

    def get_name(self):
        return "Constants"

    def get_gas_density(self, gas,  p, punit, T, Tunit, dunit):
        """Calculates the gas density with:

        .. math::

                \\frac{M}{R T} p

        :param gas: kind of gas
        :type gas: str
        :param T: Temperature array
        :type T: np.array
        :param Tunit: unit of Temperature array
        :type Tunit: str
        :param p: pessure array
        :type p: np.array
        :param punit: unit of pessure array
        :type punit: str
        :param dunit: expected unit of gas density
        :returns: gas density under given conditions
        :rtype: np.array
        """
        if Tunit == "C":
            T = T + self.get_conv("C", "K")

        p = p*self.get_conv(punit, "Pa")
        M = self.get_mol_weight(gas, "kg/mol")
        R = self.get_value("R", "Pa m^3/mol/K")

        if dunit == "kg/m^3":
            dens = M/T/R*p
            self.log.debug("calculated gas density : {}".format(dens))
            return dens

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
        if f == t:
            self.log.info("units are the same return 1")
            return np.array([1])
        else:
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
