import datetime
import time
import subprocess
import copy
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

from ..document import Document
from ..analysis import Analysis
from ..todo import ToDo
from ..values import Values
from ..constants import Constants


class Display:

    def __init__(self, doc):
        self.Cons = Constants(doc)
        self.Val = Values(doc)
        self.main_title = "id: {}".format(doc.get("_id"))
        self.plt = plt

    def add_point_no(self, x, y):
        for i, v in enumerate(x):
            self.plt.text(v, y[i], i, rotation=45.)
