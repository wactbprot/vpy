import os
import sys
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['figure.figsize']=10,10

vpy_path = '/home/ipynb/notebooks/vpy'
module_path = os.path.abspath(os.path.join(vpy_path))
if module_path not in sys.path:
    sys.path.append(module_path)

from vpy.pkg_io import Io