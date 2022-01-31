"""
python script/ce3/cal_analysis.py --ids 'cal-2021-ce3-kk-75458_0001' -u #
"""
import sys
sys.path.append(".")

import json
import numpy as np
from vpy.pkg_io import Io

def main():
    io = Io()
    io.eval_args()

    base_doc = io.get_base_doc("ce3")
    for id in io.ids:
        id = id.replace("\"", "")
        doc = io.get_doc_db(id)

        if io.update:
            doc = io.update_cal_doc(doc, base_doc)

        io.save_doc(doc)

    print(json.dumps({'ok':True}))

if __name__ == "__main__":
    main()
