import sys
import numpy as np
import couchdb
from vpy.vpy_io import Io
from vpy.standard.se3.uncert import Uncert as Se3Uncert


def main():
    io       = Io()
    base_doc = io.gen_base_doc("se3")

    se3_uncert = Se3Uncert(base_doc)


if __name__ == "__main__":
    main()
