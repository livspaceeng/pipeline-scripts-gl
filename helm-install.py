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
# branch = sys.argv[5]
org = sys.argv[5]
app_name = sys.argv[6]
lastCommit = sys.argv[7]
bitbucketCommit = sys.argv[8]

valuesDir = "values"

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
    script.append("apk --no-cache add git"+" "+"&&"+'which ssh-agent || ( apk update && apk add openssh-client )')
    script.append("eval $(ssh-agent -s)"+" "+"&&"+"""echo "$SSH_PRIIVATE_KEY2" | tr -d '\r' | ssh-add -""")
    script.append("mkdir -p ~/.ssh"+" "+"&&"+ "chmod 700 ~/.ssh"+"&&"+"""echo "$SSH_KNOWN_HOSTS" > ~/.ssh/known_hosts""" +"&&"+"chmod 644 ~/.ssh/known_hosts")
    script.append("apk update && apk add curl curl-dev && apk add bash"+" "+"&&"+"apk add --update libc-dev")
    before_script = "apk add --no-cache python3 && python3 -m ensurepip \
    && rm -r /usr/lib/python*/ensurepip && pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache"
    script.append(before_script)
    script.append("pip install pyyaml")
    script.append("helm init -c --tiller-namespace $TILLER_NAMESPACE")
    script.append("helm repo update")
    return script

def checkout(stage, org, appName, lastCommit, bitbucketCommit, pathToUpYaml, pathToDelYaml):
    script = []
    script.append("curl https://raw.githubusercontent.com/livspaceeng/pipeline-scripts-gl/master/install1.sh | bash -s latest"
)
    script.append("source /usr/local/bin/pipeline-vars.sh")
    script.append("echo "+"cloning repo")
    script.append("git clone git@bitbucket.org:"+org+"/"+app_name+".git")
    script.append("cd "+app_name)
    script.append("git checkout "+lastCommit)
    script.append("cp -r env old")
    script.append("git checkout "+bitbucketCommit)
    script.append("$CMD_DIFF old env")
    script.append("$CMD_BUILDV1"+" "+pathToUpYaml+" "+pathToDelYaml)
    script.append("cd ..")
    script.append("mkdir -p "+valuesDir)
    script.append("rm -rf "+valuesDir+"/*")
    script.append("cp /tmp/test/* "+valuesDir+"/")
    script.append("ls -la "+valuesDir)
    
    artifacts = OrderedDict()
    artifacts['paths'] = []
    artifacts['paths'].append("values")
    
    dep1 = OrderedDict()
    dep1['stage'] = stage
    dep1['script'] = script
    dep1['artifacts'] = artifacts
    return dep1
    

def buildDeployStage(stage,install, name,app,namespace,repo,version, valExists):
    valOverride = ""
    if valExists:
        valOverride = " -f "  + valuesDir + "/"+ name+".yaml"
    script = []
    script.append("echo 'Upgrading " + name + " using " + app + "'")
    
    if install:
        cmd = "helm upgrade $HELMARGS --timeout 600 --install --namespace " + namespace + " " + namespace + "-" + name + " " + repo + "/" + app + " --version " + version +  valOverride       
        for i in upYaml:
            for k,rep in reps.items():
                if i['repository'] == k and name == i['name']:
                    script.append("helm repo add " + rep['label'] + " " + rep['url'])
    else:
        cmd = "helm delete --purge "  + namespace + "-" + name
    script.append(cmd)
    env = dict()
    env['name'] = namespace
    env['url'] = glEnvUrl
    dep = OrderedDict()
    dep['stage'] = stage
    dep['script'] = script
    dep['environment'] = env
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
    
    gitlabci[deployName] = buildDeployStage("uninstall", False, deployName, apps['name'], ns, repo, apps['version'], valExists)    
    
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
    initName = "checkout" 
    initTo = "checkout"
    gitlabci[initName] = checkout(initTo, org, app_name, lastCommit, bitbucketCommit, pathToUpYaml, pathToDelYaml)
    gitlabci[deployName] = buildDeployStage(deployTo, True, deployName, apps['name'], ns, repo,apps['version'], valExists)

if done1 or done2:
    with open(glCiYaml, 'w') as outfile:
        yaml.dump(gitlabci, outfile, default_flow_style=False)
else:
    raise Exception("there is nothing to upgrade nor to delete")
