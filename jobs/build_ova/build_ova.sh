#!/bin/bash

set +e
#sudo cp ${HOME}/bin/packer   /usr/bin
#sudo apt-get install -y  jq

cd $WORKSPACE/build/packer/ansible/roles/rackhd-builds/tasks
sed -i "s#https://dl.bintray.com/rackhd/debian trusty release#https://dl.bintray.com/rackhd-mirror/debian trusty main#" main.yml
sed -i "s#https://dl.bintray.com/rackhd/debian trusty main#https://dl.bintray.com/rackhd-mirror/debian trusty main#" main.yml
cd ..

pkill packer
pkill vmware

set -x


cd $WORKSPACE/build/packer 

export PACKER_CACHE_DIR=/tmp/packer_cache
export BUILD_TYPE=vmware

#exprot vars to build ova

if [ "${IS_OFFICIAL_RELEASE}" == true ]; then
    export ANSIBLE_PLAYBOOK=rackhd_release
else
    export ANSIBLE_PLAYBOOK=rackhd_ci_builds
fi
export RACKHD_VERSION=$RACKHD_VERSION
#export end

./HWIMO-BUILD

#cd $WORKSPACE/build/packer
#curl http://rackhdci.lss.emc.com/job/BuildRelease/job/Build/job/ova-build/180/artifact/build/packer/rackhd-ubuntu-14.04-1.1.0-20170208UTC.ova -o rackhd-ubuntu-14.04.ova

mv rackhd-${OS_VER}.ova rackhd-${OS_VER}-${RACKHD_VERSION}.ova
#}

