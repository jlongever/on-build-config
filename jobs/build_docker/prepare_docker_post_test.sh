#!/bin/bash 
set -x
set -e

# Stop host mongo and rabbitmq service
# otherwise mongo and rabbitmq service won't run normally
# use host mongo and rabbitmq is a chioce but the coverage may be decreased.
# services will be restart in cleanup.sh, which script will always be executed.
echo $SUDO_PASSWORD |sudo -S service mongodb stop
echo $SUDO_PASSWORD |sudo -S service rabbitmq-server stop

rackhd_docker_images=`ls ${DOCKER_PATH}`
build_record=`ls ${DOCKER_RECORD_PATH}`

# load docker images
docker load -i $rackhd_docker_images
image_list=`head -n 1 $build_record`

pushd $BUILD_CONFIG_DIR
find ./ -type f -exec sed -i -e "s/172.31.128.1/$DOCKER_RACKHD_IP/g" {} \;
popd

pushd $RackHD_DIR/test
# in vagrant or ova， rackhd ip are all default  172.31.128.1
# but for docker containers it‘s hard to virtualize such a IP
# so replace it with DOCKER_RACKHD_IP which is usually the eth1 IP of vmslave
find ./ -type f -exec sed -i -e "s/172.31.128.1/$DOCKER_RACKHD_IP/g" {} \;
popd

# this step must behind sed replace
cd $RackHD_DIR/docker
# replace default config json with the one which is for test.
cp -f ${WORKSPACE}/build-config/vagrant/config/mongo/config.json ./monorail/config.json
#if clone file name is not repo name, this scirpt should be edited.
for repo_tag in $image_list; do
    repo=${repo_tag%:*}
    sed -i "s#${repo}.*#${repo_tag}#g" docker-compose-mini.yml
done

mkdir -p $WORKSPACE/build-deps
docker-compose -f docker-compose-mini.yml up > $WORKSPACE/build-deps/vagrant.log &

