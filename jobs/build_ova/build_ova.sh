#!/bin/bash -x

set +e

# If OVA_CACHE_BUILD is not used, cache_image directory does not exist
if [ -d  $WORKSPACE/cache_image/RackHD/packer/ ] ; then
    echo "Copy Cache images from PACKER_CACHE_BUILD job archiving"
    mv $WORKSPACE/cache_image/RackHD/packer/* $WORKSPACE/build/packer/
    ls $WORKSPACE/build/packer/*
fi

vmware -v

cd $WORKSPACE/build/packer/ansible/roles/rackhd-builds/tasks
sed -i "s#https://dl.bintray.com/rackhd/debian trusty release#https://dl.bintray.com/$CI_BINTRAY_SUBJECT/debian trusty main#" main.yml
sed -i "s#https://dl.bintray.com/rackhd/debian trusty main#https://dl.bintray.com/$CI_BINTRAY_SUBJECT/debian trusty main#" main.yml
cd ..
pkill packer
pkill vmware

set -e
cd $WORKSPACE/build/packer
#export vars to build ova
if [ "${IS_OFFICIAL_RELEASE}" == true ]; then
    export ANSIBLE_PLAYBOOK=rackhd_release
else
    export ANSIBLE_PLAYBOOK=rackhd_ci_builds
fi

if [ "$BUILD_TYPE" == "vmware" ] &&  [ -f output-vmware-iso/*.vmx ]; then
     echo "Build from template cache"
     export BUILD_STAGE=BUILD_FINAL
else
     echo "Build from begining"
     export BUILD_STAGE=BUILD_ALL
fi

export RACKHD_VERSION=$RACKHD_VERSION
#export end

./HWIMO-BUILD

mv rackhd-${OS_VER}.ova rackhd-${OS_VER}-${RACKHD_VERSION}.ova

