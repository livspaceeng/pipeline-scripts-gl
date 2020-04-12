#!/usr/bin/env python

import yaml
import sys
import hashlib
import os
import filecmp
import shutil
from collections import OrderedDict

pathToUpYaml = sys.argv[1]
pathToDelYaml = sys.argv[2]
pathToValYaml = sys.argv[3]
ns = sys.argv[4]
branch = sys.argv[5]
org = sys.argv[6]
app_name = sys.argv[7]

valuesDir = "values"
valuesDir1 = "/tmp/test"

glEnvUrl = "https://knight.livspace.com"
glImage = "alpine/helm:2.11.0"
glCiYaml = "cicd.yaml"

if 'GL_IMAGE' in os.environ:
    glImage = os.environ['GL_IMAGE']
if 'GL_ENV_URL' in os.environ:
    glEnvUrl = os.environ['GL_IMAGE']
if 'GL_CI_YAML' in os.environ:
    glCiYaml = os.environ['GL_CI_YAML']
if 'VALUES_DIR' in os.environ:
    valuesDir = os.environ['VALUES_DIR']

deployStages = []
deployOverride = dict()

def represent_dictionary_order(self, dict_data):
    return self.represent_mapping('tag:yaml.org,2002:map', dict_data.items())

def setup_yaml():
    yaml.add_representer(OrderedDict, represent_dictionary_order)

setup_yaml() 

def repoMap(repoList):
    ret = dict()
    for k in repoList:
        ret[k['url']]= k
        if 'rewrite' in k:
            k['url'] = k['rewrite']
    return ret

try:
    with open('pipeline-config.yml', 'r') as stream:
        pipeConfig = yaml.safe_load(stream)
        reps = repoMap(pipeConfig['repositories'])
        if 'stages' in pipeConfig:
            deployStages = pipeConfig['stages']
        if 'apps-stage' in pipeConfig:
            deployOverride = pipeConfig['apps-stage']
except Exception as exc:
    print(exc)
    raise exc
    
try:
    with open(pathToUpYaml, 'r') as stream:
        ups = yaml.safe_load(stream)
        upYaml = ups['dependencies']
except Exception as exc:
    print(exc)
    upYaml = []
    
try:
    with open(pathToDelYaml, 'r') as stream:
        dels = yaml.safe_load(stream)
        delYaml = dels['dependencies']
except Exception as exc:
    print(exc)
    delYaml = []
    
def getrepo(repo):
    return reps[repo]["label"]
    
def beforeScript(repo):
    script = []
    before_script= "apk --no-cache add git"
    before_script1 = 'which ssh-agent || ( apk update && apk add openssh-client )'
    before_script2 = "eval $(ssh-agent -s)"
    before_script3 = """echo "$SSH_PRIIVATE_KEY2" | tr -d '\r' | ssh-add -"""
    before_script4 = "mkdir -p ~/.ssh"
    before_script5 = "chmod 700 ~/.ssh"
    before_script6 = """echo "$SSH_KNOWN_HOSTS" > ~/.ssh/known_hosts"""
    before_script7 = "chmod 644 ~/.ssh/known_hosts"
    before_script8 = "apk update && apk add curl curl-dev && apk add bash"
    before_script9 = "apk add --update libc-dev"
    before_script10 = "apk add --no-cache python3 && python3 -m ensurepip  \
    && rm -r /usr/lib/python*/ensurepip && pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache"
    before_script11 = "pip install pyyaml"
    script.append(before_script)
    
    script.append(before_script1)
    script.append(before_script2)
    script.append(before_script3)
    script.append(before_script4)
    script.append(before_script5)
    script.append(before_script6)
    script.append(before_script7)
    script.append(before_script8)
    script.append(before_script9)
    script.append(before_script10)
    script.append(before_script11)
   
    script.append("helm init -c --tiller-namespace $TILLER_NAMESPACE")
    for k,rep in repo.items():
        script.append("helm repo add " + rep['label'] + " " + rep['url'])
    script.append("helm repo update")
    return script

def buildDeployStage(stage,install, name,app,namespace,repo,version, valExists, org, app_name):
    valOverride = ""
    if valExists:
        valOverride = " -f "  + valuesDir1 + "/"+ name+".yaml"
    
    if install:
        cmd = "helm upgrade $HELMARGS --timeout 600 --install --namespace " + namespace + " " + namespace + "-" + name + " " + repo + "/" + app + " --version " + version +  valOverride
    else:
        cmd = "helm delete --purge "  + namespace + "-" + name
    
    clone = "git clone git@bitbucket.org:"+org+"/"+app_name+".git"
    script = []
    pwd = "ls -la"+ " "+ "$pwd"
    message = "echo "+"cloning repo"
    cd = "cd "+app_name
    install = "curl https://raw.githubusercontent.com/livspaceeng/pipeline-scripts-gl/master/install1.sh | bash -s latest"
    source = "source /usr/local/bin/pipeline-vars.sh"
    checkout = "git checkout $bitbucketCommit"
    listenv = "ls -ls env"
    listenv1 = "ls -ls "+"/test/tmp"
    script.append("echo 'Upgrading " + name + " using " + app + "'")
    version1 = "python3 --version"
    version2 = "pip --version"
    version3 = "pip install pyyaml"
#     buildpython = "curl https://raw.githubusercontent.com/livspaceeng/pipeline-scripts-gl/master/buildv1.py | python -s"
    build = "$CMD_BUILDV1"
    pwd = "ls -ls $pwd"
#     "python3 buildv1.py"
    path = "ls -la "+"/usr/local/lib"
    path1 = "ls -la "+"/usr/local/bin"
    path2 = "ls -la "+"/usr/lib"
    path3 = "ls -la "+"/usr/bin"
   
    script.append(install)
    script.append(source)

    script.append(message)
    script.append(clone)
    script.append(pwd)
    script.append(cd)
    script.append(pwd)
    script.append(checkout)
    script.append(listenv)
    script.append(path)
    script.append(path1)
    script.append(path2)
    script.append(path3)
    script.append(version1)
    script.append(version2)
    script.append(version3)
    script.append(build)
    script.append(pwd)
    
    
#     script.append(buildpython)   
#     script.append(listenv1)
    
    
    
    # env = dict()
    # env['name'] = namespace
    # env['url'] = glEnvUrl

    # only= []
    # only.append(branch)
    
    dep = OrderedDict()
    dep['stage'] = stage
    dep['script'] = script
    # dep['only'] = only
    # dep['environment'] = env
    return dep
    
gitlabci = OrderedDict()
gitlabci['image'] = glImage

gitlabci['before_script'] = beforeScript(reps)

gitlabci['stages'] = deployStages


done1 = False
done2 = False

for apps in delYaml:
    done2 = True
    deployName = apps['name']
    if 'alias' in apps:
        deployName = apps['alias']
        
    repo = getrepo(apps['repository'])
    valExists = os.path.isfile(pathToValYaml + "/" +deployName + ".yaml" )
    
    gitlabci[deployName] = buildDeployStage("uninstall", False, deployName, apps['name'], ns, repo, apps['version'], valExists, org,app_name)
    
    
for apps in upYaml:
    done1 =True
    deployName = apps['name']    
    if 'alias' in apps:
        deployName = apps['alias']
        
    deployTo = "install"
    if deployName in deployOverride:
        deployTo = deployOverride[deployName]
        
    repo = getrepo(apps['repository'])
    valExists = os.path.isfile(pathToValYaml + "/" +deployName + ".yaml" )
    
    gitlabci[deployName] = buildDeployStage(deployTo, True, deployName, apps['name'], ns, repo,apps['version'], valExists, org,app_name)
    


if done1 or done2:
    with open(glCiYaml, 'w') as outfile:
        yaml.dump(gitlabci, outfile, default_flow_style=False)
else:
    raise Exception("there is nothing to upgrade nor to delete")
