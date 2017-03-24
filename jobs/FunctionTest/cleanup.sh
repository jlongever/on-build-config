#!/bin/bash -x

export VCOMPUTE=("${NODE_NAME}-Rinjin1","${NODE_NAME}-Rinjin2","${NODE_NAME}-Quanta")
VCOMPUTE="${VCOMPUTE}"
if [ -z "${VCOMPUTE}" ]; then
  VCOMPUTE=("jvm-Quanta_T41-1" "jvm-vRinjin-1" "jvm-vRinjin-2")
fi

cleanupVMs(){
    vagrantDestroy
    # Suspend any other running vagrant boxes
    vagrantSuspendAll

    # Delete any running VMs
    virtualBoxDestroyAll

    rm -rf "$HOME/VirtualBox VMs"
}

vagrantSuspendAll() {
 for box in `vagrant global-status --prune | awk '/running/{print $1}'`; do
     vagrant suspend ${box}
 done
}

vagrantDestroy() {
  cd ${WORKSPACE}/RackHD/example
  vagrant destroy -f
}

virtualBoxDestroyAll() {
  for uuid in `vboxmanage list vms | awk '{print $2}' | tr -d '{}'`; do
    echo "shutting down vm ${uuid}"
    vboxmanage controlvm ${uuid} poweroff
    echo "deleting vm ${uuid}"
    vboxmanage unregistervm ${uuid}
  done
}

nodesDelete() {
  cd ${WORKSPACE}/build-config/deployment/
  if [ "${USE_VCOMPUTE}" != "false" ]; then
    if [ $TEST_TYPE == "ova" ]; then
      VCOMPUTE+=("${NODE_NAME}-ova-for-post-test")
    fi
    for i in ${VCOMPUTE[@]}; do
      ./vm_control.sh "${ESXI_HOST},${ESXI_USER},${ESXI_PASS},delete,1,${i}_*"
    done
  fi
}

cleanupENVProcess() {
  # Kill possible socat process left by ova-post-smoke-test
  # eliminate the effect to other test
  socat_process=`ps -ef | grep socat | grep -v grep | awk '{print $2}' | xargs`
  if [ -n "$socat_process" ]; then
    kill $socat_process
  fi
}



clean_up_docker_image(){
    # parameter : the images keyword to be delete
    keyword=$1
    images=`docker images | grep ${keyword} | awk '{print $3}' | sort | uniq`
    if [ -n "$images" ]; then
        docker rmi -f $images
    fi
}

clean_running_containers() {
    local containers=$(docker ps -a -q)
    if [ "$containers" != "" ]; then
        echo "Clean Up containers : " ${containers}
        docker stop ${containers}
        docker rm  ${containers}
    fi
}

cleanupDocker(){
  # Clean UP. (was in Jenkins job post-build, avoid failure impacts build status.)
  set +e
  set -x
  echo "Show local docker images"
  docker ps
  docker images
  echo "Stop & rm all docker running containers " 
  clean_running_containers
  echo "Chown rackhd/files volume on hosts"
  echo $SUDO_PASSWORD |sudo -S chown -R $USER:$USER $WORKSPACE/RackHD 
  echo "Clean Up all docker images in local repo"
  clean_up_docker_image none
  # clean images by order, on-core should be last one because others depends on it
  clean_up_docker_image on-taskgraph
  clean_up_docker_image on-http
  clean_up_docker_image on-tftp
  clean_up_docker_image on-dhcp-proxy
  clean_up_docker_image on-syslog
  clean_up_docker_image on-tasks
  clean_up_docker_image files
  clean_up_docker_image isc-dhcp-server
  clean_up_docker_image on-wss
  clean_up_docker_image on-statsd
  clean_up_docker_image on-core
  clean_up_docker_image rackhd

  echo "clean up /var/lib/docker/volumes"
  docker volume ls -qf dangling=true | xargs -r docker volume rm
 +

}

# in jobs/build_docker/prepare_docker_post_test.sh the 2 services were stopped
# run "service start" here to ensure the 2 services is normal after testing
restart3rdServices(){
  echo $SUDO_PASSWORD |sudo -S service mongodb start
  echo $SUDO_PASSWORD |sudo -S service rabbitmq-server start
}

cleanupVMs
nodesDelete
cleanupENVProcess
cleanupDocker
restart3rdServices
