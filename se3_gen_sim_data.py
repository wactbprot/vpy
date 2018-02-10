import json

def main():

    sim_doc = {"Temperature":[]}

    with open('./vpy/standard/se3/types.json') as json_types_file:
        types = json.load(json_types_file)

    for measurand in sim_doc:
        for subm in types[measurand]:
            for v in types[measurand][subm]:
                entr = {"Type":v["Type"],
                        "Value":v["Sim"],
                        "Unit":v["Unit"]}
                sim_doc[measurand].append(entr)

    print(sim_doc)
if __name__ == "__main__":
    main()
