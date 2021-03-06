#!/usr/bin/env python3.8

import yaml
import sys
from os import mkdir, walk
import datetime

UpdatedYaml = sys.argv[1]
DeletedYaml = sys.argv[2]

VALUE_DIR = 'env/values'
VALUE_FILE_NAME = 'values.yaml'
OUT_DIR="/tmp/test"

print("Output directory " + OUT_DIR)

try:  
    mkdir(OUT_DIR)
except OSError:  
    print ("Creation of the directory %s failed " % OUT_DIR)
else:  
    print ("Successfully created the directory %s " % OUT_DIR)

reqsUpdated = yaml.load(open(UpdatedYaml),Loader=yaml.FullLoader)
depsUpdated = reqsUpdated["dependencies"]

reqsDeleted = yaml.load(open(DeletedYaml),Loader=yaml.FullLoader)
depsDeleted = reqsDeleted["dependencies"]

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

for m in depsUpdated:
    version = m['version']
    repo = m['repository']
    release = m['name']
    value = {}
    name = m['name']
    if 'alias' in m:
        name = m['alias']
    value = MergeValues(name)
    with open(OUT_DIR + "/" + name + '.yaml', 'w') as outfile:
        yaml.dump(value, outfile, default_flow_style=False, allow_unicode=True,width=1000)
    
for m in depsDeleted:
    version = m['version']
    repo = m['repository']
    release = m['name']
    value = {}
    name = m['name']
    if 'alias' in m:
        name = m['alias']
    value = MergeValues(name)
   
    with open(OUT_DIR + "/" + name + '.yaml', 'w') as outfile:
        yaml.dump(value, outfile, default_flow_style=False, allow_unicode=True,width=1000)
