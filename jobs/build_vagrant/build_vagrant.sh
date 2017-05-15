#!/bin/bash -x
set +e
ifconfig
packer -v
vagrant -v

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

mv $WORKSPACE/cache_image/RackHD/packer/* $WORKSPACE/build/packer/
ls $WORKSPACE/build/packer/*

pushd $WORKSPACE/build/packer/ansible/roles/rackhd-builds/tasks
sed -i "s#https://dl.bintray.com/rackhd/debian trusty release#https://dl.bintray.com/$CI_BINTRAY_SUBJECT/debian trusty main#" main.yml
sed -i "s#https://dl.bintray.com/rackhd/debian trusty main#https://dl.bintray.com/$CI_BINTRAY_SUBJECT/debian trusty main#" main.yml
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
