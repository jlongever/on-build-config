#!/bin/bash

ifconfig

set +e

packer -v
vagrant -v

cd $WORKSPACE/build/packer/ansible/roles/rackhd-builds/tasks


############# DEBUG ######################20160117  for 1.0.0 release
###rm main.yml
###wget https://raw.githubusercontent.com/panpan0000/RackHD/ForceAptUpdate/packer/ansible/roles/rackhd-builds/tasks/main.yml
############# DEBUG ######################


sed -i "s#https://dl.bintray.com/rackhd/debian trusty release#https://dl.bintray.com/rackhd-mirror/debian trusty main#" main.yml
sed -i "s#https://dl.bintray.com/rackhd/debian trusty main#https://dl.bintray.com/rackhd-mirror/debian trusty main#" main.yml
pkill packer

cd ..

cd $WORKSPACE/build/packer 


export PACKER_CACHE_DIR=/tmp/packer_cache


#exprot vars to build virtualbox
if [ "${IS_OFFICIAL_RELEASE}" == "true" ]; then
    export ANSIBLE_PLAYBOOK=rackhd_release
else
    export ANSIBLE_PLAYBOOK=rackhd_ci_builds
fi
export UPLOAD_BOX_TO_ATLAS=false
export RACKHD_VERSION=$RACKHD_VERSION
#export end

#build
./HWIMO-BUILD


#cd $WORKSPACE/build/packer

#curl http://rackhdci.lss.emc.com/job/BuildRelease/job/Build/job/vagrant-build/211/artifact/build/packer/rackhd-ubuntu-14.04-1.1.0-20170208UTC.box  -o packer_virtualbox-iso_virtualbox.box

#post process
PACKERDIR="$WORKSPACE/build/packer/"
BOX="$PACKERDIR/packer_virtualbox-iso_virtualbox.box"
if [ -e "$BOX" ]; then
  mv "$BOX" "$PACKERDIR/rackhd-${OS_VER}-${RACKHD_VERSION}.box"
fi


