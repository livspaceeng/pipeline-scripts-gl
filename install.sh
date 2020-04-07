#!/bin/bash

version="latest"
if [ ! -z $1 ]; then
	version=$1
fi

echo "Using version $version"
echo "To use different version, pass the first argument as version values."
echo "Possible versions are branch name and tags"

rm -rf /tmp/latest.zip /tmp/scripts
curl -L -o /tmp/latest.zip https://github.com/namannagar/environment-jx-beta-NN/archive/${version}.zip
mkdir /tmp/scripts
cd /tmp/scripts
unzip -j /tmp/latest.zip

chmod +x *

mv * /usr/local/bin/

pip install PyYaml
