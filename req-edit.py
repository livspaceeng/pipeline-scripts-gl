import yaml
import sys

REQ = sys.argv[1]
APP = sys.argv[2]
VERSION = sys.argv[3]

with open(REQ,'r') as file:
    # The FullLoader parameter handles the conversion from YAML
    # scalar values to Python the dictionary format
    deps = yaml.load(file, Loader=yaml.FullLoader)
    done = False

    for app in deps["dependencies"]:
        if app["name"] == APP and "alias" not in app:
            app["version"] = VERSION
            done = True
            break

    if not done:
        print("App doest exist in the file already, adding a new entry")
        ent  = dict()
        ent["name"] = APP
        ent["repository"] = "http://jenkins-x-chartmuseum:8080"
        ent["version"] = VERSION
        deps["dependencies"].append(ent)

    with open('output.yaml', 'w') as outfile:
        yaml.dump(deps, outfile, default_flow_style=False)  
