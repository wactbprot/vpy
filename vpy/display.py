import datetime
import time
import subprocess
import copy
import numpy as np
from .document import Document
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from .analysis import Analysis
from .todo import ToDo
from .values import Pressure, Temperature


class Display(Document):
    """Holds a deep copy of ``document``.
    """

    def __init__(self, doc):

        super().__init__(None)
        self.org = copy.deepcopy(doc)


    def show(self):
        T = Document(self.org.get('Calibration', {}).get('Measurement', {}).get('Values', {}).get('Temperature', {}))
        T.get_value('T_room', 'C')
        T_val, T_unit = T.get_value_and_unit('T_room')
        print("**here!**")
        print(T_val, T_unit)