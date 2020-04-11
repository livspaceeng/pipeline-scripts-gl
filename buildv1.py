#!/usr/bin/env python

import yaml
import sys
from os import mkdir, walk
import datetime

REQ_FILE ='env/requirements.yaml'
VALUE_DIR = 'env/values'
VALUE_FILE_NAME = 'values.yaml'
OUT_DIR="/tmp/test"
NAMESPACE='test'

if len(sys.argv) >= 2 and sys.argv[1] is not None:
    OUT_DIR = sys.argv[1]
if len(sys.argv) >= 3 and sys.argv[2] is not None:
    NAMESPACE = sys.argv[2]

print("Output directory " + OUT_DIR)
print("Deployment namespace is  " + NAMESPACE)

try:  
    mkdir(OUT_DIR)
except OSError:  
    print ("Creation of the directory %s failed " % OUT_DIR)
else:  
    print ("Successfully created the directory %s " % OUT_DIR)

reqs = yaml.load(open(REQ_FILE),Loader=yaml.FullLoader)
deps = reqs["dependencies"]

def str_presenter(dumper, data):
    dlen = 0
    style = None
    try:
        dlen = len(data.splitlines())
    except TypeError as ex:
        print(ex) 
    if (dlen > 1):
        style='|' 
     
    print("Using style %s for data: %s" % (style,data))
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style=style)

def BuildHR(name,namespace,repo,repo_name,version,value):
    hr = dict()
    metadata = dict()
    spec = dict()
    chart = dict()

    spec["chart"] = chart
    hr["spec"] = spec
    hr["metadata"] = metadata
    hr['apiVersion'] = "flux.weave.works/v1beta1"
    hr['kind'] = "HelmRelease"

    metadata["name"] = name
    metadata["namespace"] = namespace

    chart["repository"] = repo
    chart["name"] = repo_name
    chart["version"] =  version

    spec["values"] = value
    return hr

def MergeValues(name):
    d = VALUE_DIR + "/" + name

    try:
        value = yaml.load(open(d + "/" + VALUE_FILE_NAME),Loader=yaml.FullLoader)
    except yaml.YAMLError as exc:
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            print("Error position: (%s:%s)" % (mark.line+1, mark.column+1))
        return dict()
    except IOError as e:
        print(e)
        return dict()

    files = dict()
    for (dirpath, dirnames, filenames) in walk(d):
        for f in filenames:
            if f != VALUE_FILE_NAME:
                with open(dirpath + "/" + f, 'r') as myfile:
                    #Becuase of issue https://github.com/yaml/pyyaml/issues/121
                    output = ''
                    for line in myfile:
                        output = output + line.rstrip()  + "\n"
                    files[f] = output
    if name == "expose":
        value['Annotations']['helmrelease'] = datetime.datetime.utcnow().isoformat()

    if 'config' in value and 'enabled' in value['config'] and value['config']['enabled']:
        value['config']['files'] = files

    return value

yaml.add_representer(str, str_presenter)
#yaml.add_representer(bytes, str_presenter)
#yaml.representer.BaseRepresenter.represent_scalar = my_represent_scalar

for m in deps:
    version = m['version']
    repo = m['repository']
    release = m['name']
    value = {}
    name = m['name']
    if 'alias' in m:
        name = m['alias']
    value = MergeValues(name)
    hr = BuildHR(name,NAMESPACE,repo,release,version,value)

    #yaml.add_representer(str, str_presenter)
    # yaml.add_representer(unicode, str_presenter)

    with open(OUT_DIR + "/" + name + '.yaml', 'w') as outfile:
        yaml.dump(value, outfile, default_flow_style=False, allow_unicode=True,width=1000)
    # print(yaml.dump(hr,default_flow_style=False))
