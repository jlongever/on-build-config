#!/bin/bash -ex
export VCOMPUTE=("${NODE_NAME}-Rinjin1","${NODE_NAME}-Rinjin2","${NODE_NAME}-Quanta")

VCOMPUTE="${VCOMPUTE}"
if [ -z "${VCOMPUTE}" ]; then
  VCOMPUTE=("jvm-Quanta_T41-1" "jvm-vRinjin-1" "jvm-vRinjin-2")
fi


nodesDelete() {
  cd ${WORKSPACE}/build-config/deployment/
  if [ "${USE_VCOMPUTE}" != "false" ]; then
    VCOMPUTE+=("${NODE_NAME}-ova-for-post-test")
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

clean_running_containers() {
    local containers=$(docker ps -a -q)
    if [ "$containers" != "" ]; then
        echo "Clean Up containers : " ${containers}
        docker stop ${containers}
        docker rm  ${containers}
    fi
}

if [ "$SKIP_PREP_DEP" == false ] ; then
  # Prepare the latest dependent repos to be shared with vagrant
  nodesDelete
  cleanupENVProcess
  clean_running_containers
fi
