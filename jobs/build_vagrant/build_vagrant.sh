#!/bin/bash -x
set +e
ifconfig
packer -v  # $? of "packer -v" is 1 ...
vagrant -v
set -e

echo "Modify rackhd-builds ansible role to redirect to Artifactory: "$ARTIFACTORY_URL

cleanup()
{
    if [ "$(echo $flags|grep e)" != "" ]; then
        e_flag=true
    fi

    set +e
   
    pkill packer
    pushd $WORKSPACE/on-build-config/jobs/build_vagrant/
    ./cleanup_vbox.sh
    popd
    #restore original "set -e" flag
    if [ "$e_flag" == "true" ]; then
       set -e
    fi
}
if [ -d  $WORKSPACE/cache_image/RackHD/packer/ ] ; then
     echo "Copy Cache images from PACKER_CACHE_BUILD job archiving"
     mv $WORKSPACE/cache_image/RackHD/packer/* $WORKSPACE/build/packer/
     ls $WORKSPACE/build/packer/*
fi

pushd $WORKSPACE/build/packer/ansible/roles/rackhd-builds/tasks
sed -i "s#https://dl.bintray.com/rackhd/debian trusty release#${ARTIFACTORY_URL}/${STAGE_REPO_NAME} ${DEB_DISTRIBUTION} ${DEB_COMPONENT}#" main.yml
sed -i "s#https://dl.bintray.com/rackhd/debian trusty main#${ARTIFACTORY_URL}/${STAGE_REPO_NAME} ${DEB_DISTRIBUTION} ${DEB_COMPONENT}#" main.yml
popd

cleanup # clean up previous dirty env

set -e
pushd $WORKSPACE/build/packer

if [ "$BUILD_TYPE" == "virtualbox" ] &&  [ -f output-virtualbox-iso/*.ovf ]; then
     echo "Build from template cache"
     export BUILD_STAGE=BUILD_FINAL
else
     echo "Build from begining"
     export BUILD_STAGE=BUILD_ALL
fi

export PACKER_CACHE_DIR=$HOME/.packer_cache

if [ "${IS_OFFICIAL_RELEASE}" == "true" ]; then
    export ANSIBLE_PLAYBOOK=rackhd_release
else
    export ANSIBLE_PLAYBOOK=rackhd_ci_builds
fi
export UPLOAD_BOX_TO_ATLAS=false
export RACKHD_VERSION=$RACKHD_VERSION
#export end

#cleanup whenever the script exits
trap cleanup  SIGINT SIGTERM SIGKILL EXIT 


#build
./HWIMO-BUILD

PACKERDIR="$WORKSPACE/build/packer/"
BOX="$PACKERDIR/rackhd-${OS_VER}.box"
if [ -e "$BOX" ]; then
  mv "$BOX" "$PACKERDIR/rackhd-${OS_VER}-${RACKHD_VERSION}.box"
fi

popd
