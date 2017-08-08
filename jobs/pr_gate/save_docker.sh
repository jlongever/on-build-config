#!/bin/bash -x
set +e
docker_tag="${1,,}"
echo $SUDO_PASSWORD |sudo -S docker login -u $DOCKERHUB_USER -p $DOCKERHUB_PASSWD
containerId=$( echo $SUDO_PASSWORD |sudo -S docker ps|grep "my/test" | awk '{print $1}' )
echo $SUDO_PASSWORD |sudo -S docker commit $containerId my/prgate
echo $SUDO_PASSWORD |sudo -S docker tag my/prgate rackhdci/$docker_tag
echo $SUDO_PASSWORD |sudo -S docker push rackhdci/$docker_tag

echo "Please run below command to run the docker locally:" > ${WORKSPACE}/build-log/docker_tag.log
echo "sudo docker run --net=host -d -t rackhdci/${docker_tag}" >> ${WORKSPACE}/build-log/docker_tag.log
echo "PS: the docker require a NIC with ip 172.31.128.250" >> ${WORKSPACE}/build-log/docker_tag.log

