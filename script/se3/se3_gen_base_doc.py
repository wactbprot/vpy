import json
import sys
import os
sys.path.append(os.environ["VIRTUAL_ENV"])

from vpy.pkg_io import Io

def main():
    io = Io()
    doc = io.get_base_doc("se3")

    with open("vpy/standard/se3/base_doc.json", 'w') as f:
            json.dump(doc, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
