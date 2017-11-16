import copy
import numpy as np
import sympy as sym

from ..vpy_io import Io
from ..document import Document
from ..standard.standard import Standard
from ..device.srg import Srg
from ..constants import Constants
from ..calibration_devices import  CalibrationObject
from ..values import Temperature, Pressure, Time, AuxFrs5


class Frs5(Standard):
    """Calculation methods of large area piston gauge FRS5.

            * ``p_frs``    ... abs. pressure of the piston gauge [p]=Pa
            * ``r``        ... reading [r] = lb
            * ``u_b``      ... standard uncertainty of the balance [u_b] = lb (4.4e-6+5e-6*R)
            * ``u_sys``    ... sys. uncertanty of the balance [u_sys]=lb (1e-5*R)
            * ``r_0``      ... zero reading [r_0] = lb
            * ``A``        ... effective area [A]= m^2
            * ``p_res``    ... residual pressure [p.res]=Pa
            * ``m_cal``    ... calibration mass piece [m.cal]=kg
            * ``rho_gas``  ... density gas
            * ``rho_frs``  ... density frs piston
            * ``g``        ... accelaration [g]=m/s^2
            * ``r_cal``    ... indication at m_cal [r_cal]=g
            * ``r_cal_0``  ...  indication at zero [r_cal_0]=g
            * ``ab``       ... temperatur coeff. [k]=1/K
            * ``t``        ... temperature of balance [t]=C

            model equation:

            .. math::

                p=\\frac{r_{ind}-r_0+u_b+u_{sys}}{r_{cal}-r_{cal 0}}\\
                 m_{cal}\\frac{g}{A_{eff}}\\frac{1}{corr_{rho}corr_{tem}}
    """
    name  = "FRS5"
    unit  = "mbar"


    def __init__(self, orgdoc):
        super().__init__(orgdoc, self.name)

        self.log = Io().logger(__name__)

        doc = copy.deepcopy(orgdoc)
        # measurement values
        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Time = Time(doc)
        self.Aux  = AuxFrs5(doc)

        # residua pressure device
        self.ResDev = Srg(doc, self.Cobj.get_by_name("FRS55_4019"))
        self.no_of_meas_points = len(self.Time.get_value("amt_frs5_ind", "ms"))


    def get_name(self):
        """Returns the name of the standard

        :returns: name of standard
        :rtype: str
        """
        return self.name

    def get_gas(self):
        """Returns the name of the calibration gas stored in *AuxValues*

        .. todo::

                implementation of aux.gas needed

        """

        self.log.warn("Default gas N2 used")
        return "N2"

    def define_model(self, res):
        """ Defines symbols and model for FRS5.
        The order of symbols must match the order in ``gen_val_arr``:

        #. A
        #. r
        #. r_0
        #. r_cal
        #. r_cal0
        #. ub
        #. usys
        #. p_res
        #. m_cal
        #. g
        #. tem
        #. rho_frs
        #. rho_gas
        #. ab

        """
        A          = sym.Symbol('A')
        p_res      = sym.Symbol('p_res')
        m_cal      = sym.Symbol('m_cal')
        g          = sym.Symbol('g')
        tem        = sym.Symbol('tem')
        rho_frs    = sym.Symbol('rho_frs')
        rho_gas    = sym.Symbol('rho_gas')
        ab         = sym.Symbol('ab')
        r_cal      = sym.Symbol('r_cal')
        r_cal0     = sym.Symbol('r_cal0')
        r          = sym.Symbol('r')
        r_0        = sym.Symbol('r_0')
        ub         = sym.Symbol('ub')
        usys       = sym.Symbol('usys')

        self.symb = (
                A,r,r_0,r_cal,r_cal0,ub,usys,p_res,m_cal,g,tem,rho_frs,rho_gas,ab,)

        self.model = sym.S(
                (r-r_0+ub+usys)/(r_cal-r_cal0)
                *m_cal
                *g/A
                *1.0/(1.0-rho_gas/rho_frs)
                *1.0/(1.0+ab*(tem-20.0))
                +p_res)

    def gen_val_array(self, res):
        """Generates a array of values
        with the same order as ``define_model``s symbols order:

        #. A
        #. r
        #. r_0
        #. r_cal
        #. r_cal0
        #. ub
        #. usys
        #. p_res
        #. m_cal
        #. g
        #. tem
        #. rho_frs
        #. rho_gas
        #. ab

        """

        mt       = self.Time.get_value("amt_frs5_ind", "ms")
        r_zc0    = self.Aux.get_val_by_time(mt, "offset_mt", "ms", "frs_zc0_p", "lb")
        r_zc     = self.Pres.get_value("frs_zc_p", "lb")

        self.val_arr = [ self.get_value("A_eff","m^2"),
                self.Pres.get_value("frs_p", "lb"),
                r_zc-r_zc0,
                self.get_value("R_cal","lb"),
                np.full(self.no_of_meas_points, 0.0),
                np.full(self.no_of_meas_points, 0.0),
                np.full(self.no_of_meas_points, 0.0),
                res.pick("Pressure", "frs5_res", self.unit),
                self.get_value("m_cal","kg"),
                self.get_value("g_frs","m/s^2"),
                res.pick("Temperature", "frs5", "C"),
                self.get_value("rho_frs", "kg/m^3"),
                self.get_value("rho_gas","kg/m^3"),
                self.get_value("alpha_beta_frs", "1/C"),
                ]

    def uncertainty(self, res):
        """Calculates the total uncertainty.
        sympy derives the sensitivity coefficients.

        """
        self.define_model(res)
        self.gen_val_array(res)
        self.uncert_r(res)
        self.uncert_r_0(res)
    #
    #    s_m_cal      = sym.diff(p_frs, m_cal)
    #    s_g          = sym.diff(p_frs, g)
    #    s_A          = sym.diff(p_frs, A)
    #    s_tem        = sym.diff(p_frs, tem)
    #    s_tem        = sym.diff(p_frs, tem)
    #    s_rho_gas    = sym.diff(p_frs, rho_gas)
    #    s_rho_frs    = sym.diff(p_frs, rho_frs)
#
    #    u_A       = self.get_expression("u_A", "m^2")
    #    u_m_cal   = self.get_expression("u_m_cal", "kg")
    #    u_rho_frs = self.get_expression("u_rho_frs", "kg/m^3")
#
    #    # relative uncertainties
    #    u_g      = self.get_expression("u_g", "1") * self.g
#
    #    # gas dependend
    #    gas = self.get_gas()
    #    u_rho_gas  = self.get_expression("u_rho_frs", "kg/m^3")
#
#
    #    s_r_cal      = sym.diff(self.model, r_cal)
    #    s_r_cal0     = sym.diff(self.model, r_cal0)
#
    #    u_r_cal   = self.get_expression("u_r_cal", "lb")
    #    u_r_cal0  = self.get_expression("u_r_cal0", "lb")


    def uncert_r(self, res):
        """Calculates the uncertainty of the r (reading)

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        conv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "frs5", self.unit)

        s_expr = sym.diff(self.model, sym.Symbol('r'))
        u_expr = self.get_expression("u_r", "lb")

        f     = sym.lambdify(self.symb, s_expr * u_expr , "numpy")
        val   = f(*self.val_arr)*conv

        res.store("Uncertainty", "r", np.absolute(val/p), "1")



    def uncert_r_0(self, res):
        """Calculates the uncertainty of the r_0 (offset)

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """
        conv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "frs5", self.unit)

        s_expr = sym.diff(self.model, sym.Symbol('r_0'))
        u_expr = self.get_expression("u_r_0", "lb")

        f     = sym.lambdify(self.symb, s_expr * u_expr , "numpy")
        val   = f(*self.val_arr)*conv

        res.store("Uncertainty", "r_0", np.absolute(val/p), "1")

    def uncert_ub(self, res):
        """Calculates the uncertainty of the r (reading)

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        conv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "frs5", self.unit)

        s_expr = sym.diff(self.model, sym.Symbol('ub'))
        u_expr = self.get_expression("u_ub", "lb")

        f     = sym.lambdify(self.symb, s_expr * u_expr , "numpy")
        val   = f(*self.val_arr)*conv

        res.store("Uncertainty", "ub", np.absolute(val/p), "1")

    def uncert_usys(self, res):
        """Calculates the uncertainty of the r (reading)

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        s_usys  = sym.diff(self.model, sym.Symbol('usys') )
        u_usys  = self.get_expression("u_usys", "lb")

    def pressure_res(self, res):
        """Calculates the residual Pressure from
        SRG-DCR values.
        """

        tem = self.Temp.get_obj("frs5", "C")
        gas = self.Aux.get_gas()
        mt  = self.Time.get_value("amt_frs5_ind", "ms")

        off = self.Aux.get_obj_by_time(mt, "offset_mt", "ms", "frs_res_off", "DCR")
        res_off = self.ResDev.pressure(off, tem, "mbar", gas)

        ind     = self.Pres.get_obj("frs_res_ind", "DCR")
        res_ind = self.ResDev.pressure(ind, tem, "mbar", gas)

        res.store('Pressure',"frs5_res_off", res_off, "mbar")
        res.store('Pressure',"frs5_res_ind", res_ind, "mbar")
        res.store('Pressure',"frs5_res", res_ind - res_off , "mbar")

    def temperature(self, res):
        tem      = self.Temp.get_value("frs5", "C")
        res.store('Temperature',"frs5", tem , "C")


    def pressure_cal(self, res):
        """Calculates the FRS5 calibration pressure from
        lb indication. The equation is:


        .. math::

            p=\\frac{r}{r_{cal}} m_{cal}\\frac{g}{A_{eff}}\\
                \\frac{1}{corr_{rho}corr_{tem}} + p_{res}

        with

        .. math::

                corr_{rho} = 1 - \\frac{\\rho_{gas}}{\\rho_{piston}}

        and

        .. math::

                corr_{tem} = 1 + \\alpha \\beta (\\vartheta - 20)
        """

        # constants of standard
        A        = self.get_value("A_eff","m^2")
        g        = self.get_value("g_frs","m/s^2")
        r_cal    = self.get_value("R_cal","lb")
        m_cal    = self.get_value("m_cal","kg")
        rho_frs  = self.get_value("rho_frs", "kg/m^3")
        rho_gas  = self.get_value("rho_gas","kg/m^3")
        ab       = self.get_value("alpha_beta_frs", "1/C")
        r        = self.Pres.get_value("frs_p", "lb")
        tem      = res.pick("Temperature", "frs5", "C")
        p_res    = res.pick("Pressure", "frs5_res", self.unit)

        # correction buoyancy
        corr_rho = (1.0-rho_gas/rho_frs)
        corr_rho = np.full(self.no_of_meas_points, corr_rho)

        # correction temperature
        corr_tem = (1.0 + ab * (tem - 20.0))

        # conversion Pa  to unit
        conv     = self.Cons.get_conv("Pa", self.unit)
        # conversion lb to Pa
        f = m_cal/r_cal*g/(A*corr_rho * corr_tem) # Pa

        # offset reading
        mt    = self.Time.get_value("amt_frs5_ind", "ms")
        r_zc0 = self.Aux.get_val_by_time(mt, "offset_mt", "ms", "frs_zc0_p", "lb")
        r_zc  = self.Pres.get_value("frs_zc_p", "lb")
        r_0   = r_zc-r_zc0

        # offset pressure
        p_0 = r_0*f*conv
        # indication
        p_corr   = r*f*conv - p_0 + p_res

        res.store("Correction", "buoyancy_frs5", corr_rho, "1")
        res.store("Correction", "temperature_frs5", corr_tem, "1")
        res.store('Pressure', "frs5_off", p_0, self.unit)
        res.store('Pressure', "frs5", p_corr, self.unit)
