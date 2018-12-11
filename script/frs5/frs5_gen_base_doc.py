import json
from vpy.pkg_io import Io

def main():
    io = Io()
    doc = io.get_base_doc("frs5")

    with open("vpy/standard/frs5/base_doc.json", 'w') as f:
            json.dump(doc, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
