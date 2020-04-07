#!/bin/bash

APP_NAME=$1
APPVERSION=$2
ENV=$3

reqFile="env/requirements.yaml"
beta="https://${BB_USER_ID}:${BB_USER_TOKEN}@bitbucket.org/livspaceeng/environment-jx-beta.git"
dev="https://${BB_USER_ID}:${BB_USER_TOKEN}@bitbucket.org/livspaceeng/environment-jx-dev.git"

rm -rf /tmp/env || echo "No cleanup required, /tmp/env doesnt exist"
mkdir /tmp/env && cd /tmp/env
if [ $ENV == "master" ]; then
  envname="beta"
  echo "Cloning repo ${beta}"
  git clone "${beta}"  .
elif [ $ENV == "build" ]; then
  envname="dev"
  echo "Cloning repo ${dev}"
  git clone "${dev}"  .
else
  echo "No deployment mapped, Exit."
  exit 0
fi
echo "Upgrading version of $APP_NAME in ENV: $envname to $APPVERSION"
git config --global user.name "${CI_BOT_USER}"
git config --global user.email "${CI_BOT_EMAIL}"
rm -rf output.yaml || echo "output.yaml doesnt exist"
python /tmp/scripts/req-edit.py "$reqFile" $APP_NAME $APPVERSION
cp output.yaml $reqFile
git add $reqFile
git commit -m "Upgrading version of $APP_NAME in ENV($envname) to $APPVERSION"
git push origin master
