#!/usr/bin/env python

import yaml
import sys
import hashlib
import os
import filecmp
import shutil

FOLDER1 = sys.argv[1]
FOLDER2 = sys.argv[2]
map1 = dict()
map2 = dict()
yaml1 = dict()
yaml2 = dict()

delYaml = dict()
delList = []
delYaml2 = dict()
upYaml = dict()
upList = []
upYaml2 = dict()

map_for_file_deletion = {}
doFull = False

def getNameForRepo(repo):
    name = repo['name']
    if 'alias' in repo:
        name = repo['alias']
    return name

try:
    with open(FOLDER1 + "/requirements.yaml", 'r') as stream:
        yaml1 = yaml.safe_load(stream)
except OSError as exc:
    doFull = True
    print(exc)
except yaml.YAMLError as exc:
    print(exc)
    raise exec

try:
    with open(FOLDER2 + "/requirements.yaml", 'r') as stream:
        yaml2 = yaml.safe_load(stream)
except Exception as exc:
    print(exc)
    raise exc

try:
  shutil.rmtree("result")
except Exception as e:
  print(e)
  print("Error in removing result dir")
os.mkdir("result")

if doFull:
    with open('result/updatedReposList.yaml', 'w') as outfile:
        yaml.dump(yaml2, outfile, default_flow_style=False)
    sys.exit(0)

try:
    for k in yaml1['dependencies']:
	    map1[getNameForRepo(k)] = k
    for l in yaml2['dependencies']:
	    map2[getNameForRepo(l)] = l
except Exception as e:
    print(e)

for repo in map1:
    if repo not in map2:
        delYaml[repo] = map1[repo]
        delList.append(map1[repo])
    elif map1[repo] != map2[repo]:
        upYaml[repo] = map2[repo]
        upList.append(map2[repo])
for repo in map2:
    if repo not in map1:
        upYaml[repo] = map2[repo]
        upList.append(map2[repo])

if "expose" in map2:
    upYaml["expose"] = map2["expose"]
    upList.append(map2["expose"])


filecmp.clear_cache()
for subdir, dirs, files in os.walk(FOLDER1+'/values'):
    try:
      dir_name = subdir.split('/values/')[1]
      dcmp = filecmp.dircmp(FOLDER1+ '/values/'+ dir_name ,FOLDER2 + '/values/'+ dir_name)
      for sub, dir, files in os.walk(FOLDER1+'/values/' + dir_name):
         map_for_file_deletion[dir_name] = files
      for sub, dir, files in os.walk(FOLDER2+'/values/' + dir_name):
         if dir_name not in map_for_file_deletion:
           upYaml[dir_name] = map2[dir_name]
           upList.append(map2[dir_name])
         if dir_name in map_for_file_deletion and len(map_for_file_deletion[dir_name]) != len(files):
           upYaml[dir_name] = map2[dir_name]
           upList.append(map2[dir_name])
      if len(dcmp.diff_files) > 0:
         upYaml[dir_name] = map2[dir_name]
         upList.append(map2[dir_name])
    except Exception as e:
	    print(e)
	    print("Skipping", subdir)

delYaml2['dependencies'] = delList
upYaml2['dependencies'] = upList

#lines = ""
#for up in upYaml:
#  lines = lines + "u,"+ upYaml[up]["name"] + "," + upYaml[up]["repository"] + "," + upYaml[up]["version"] +"\n"
#for dele in delYaml :
#  lines = lines + "d,"+ delYaml[dele]["name"] + "," + delYaml[dele]["repository"] + "," + delYaml[dele]["version"] +"\n"#

#with open("result/final.txt", "a") as myfile:
#    myfile.write(lines)

#print("Changes will be written to updatedRepos.yaml and deletedRepos.yaml!")
#with open('result/updatedRepos.yaml', 'w') as outfile:
#    yaml.dump(upYaml, outfile, default_flow_style=False)
#with open('result/deletedRepos.yaml', 'w') as outfile:
#    yaml.dump(delYaml, outfile, default_flow_style=False)
    
with open('result/updatedReposList.yaml', 'w') as outfile:
    yaml.dump(upYaml2, outfile, default_flow_style=False)
with open('result/deletedReposList.yaml', 'w') as outfile:
    yaml.dump(delYaml2, outfile, default_flow_style=False)
