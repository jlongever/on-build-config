#!/bin/bash +xe
REPO_NAME=`pushd ${WORKSPACE}/build >/dev/null && git remote show origin -n | grep "Fetch URL:" | sed "s#^.*/\(.*\).git#\1#" && popd > /dev/null`
VCOMPUTE=("jvm-Quanta_T41-1" "jvm-vRinjin-1" "jvm-vRinjin-2")
REPOS=("on-http" "on-taskgraph" "on-dhcp-proxy" "on-tftp" "on-syslog")
HTTP_STATIC_FILES="${HTTP_STATIC_FILES}"
TFTP_STATIC_FILES="${TFTP_STATIC_FILES}"
if [ ! -z "${1}" ]; then
  HTTP_STATIC_FILES=$1
fi
if [ ! -z "${2}" ]; then
  TFTP_STATIC_FILES=$2
fi

dlHttpFiles() {
  dir=${WORKSPACE}/build/static/http/common
  if [ "${REPO_NAME}" != "on-http" ]; then
      dir=${WORKSPACE}/build-deps/on-http/static/http/common
  fi
  mkdir -p ${dir} && cd ${dir}
  for i in ${HTTP_STATIC_FILES}; do
     wget --no-check-certificate https://bintray.com/artifact/download/rackhd/binary/builds/${i}
  done
}

dlTftpFiles() {
  dir=${WORKSPACE}/build/static/tftp
  if [ "${REPO_NAME}" != "on-tftp" ]; then
      dir=${WORKSPACE}/build-deps/on-tftp/static/tftp
  fi
  mkdir -p ${dir} && cd ${dir}
  for i in ${TFTP_STATIC_FILES}; do
    wget --no-check-certificate https://bintray.com/artifact/download/rackhd/binary/ipxe/${i}
  done
}

prepareDeps() {
  rm -rf ${WORKSPACE}/build-deps
  mkdir -p ${WORKSPACE}/build-deps/${REPO_NAME} 
  for i in ${REPOS[@]}; do
     cd ${WORKSPACE}/build-deps
     if [ "${i}" != "${REPO_NAME}" ]; then
         git clone https://github.com/RackHD/${i}.git
         cd ${i} && npm install --production
     fi
  done
  dlTftpFiles
  dlHttpFiles
}

nodesOff() {
  cd ${WORKSPACE}/tools/deployment/
  for i in ${VCOMPUTE[@]}; do
    ./scale_out_infras_operation.sh "${ESXI_HOST},${ESXI_USER},${ESXI_PASS},power_off,1,${i}_*"
  done
}

nodesOn() {
  cd ${WORKSPACE}/tools/deployment/
  for i in ${VCOMPUTE[@]}; do
    ./scale_out_infras_operation.sh "${ESXI_HOST},${ESXI_USER},${ESXI_PASS},power_on,1,${i}_*"
  done
}

vagrantUp() {
  cd ${WORKSPACE}/RackHD/example
  cp -rf ${WORKSPACE}/build-config/vagrant/* .
  WORKSPACE=${WORKSPACE} REPO_NAME=${REPO_NAME} vagrant up --provision
}

vagrantDestroy() {
  cd ${WORKSPACE}/RackHD/example
  vagrant destroy -f
}

vagrantHalt() {
  cd ${WORKSPACE}/RackHD/example
  vagrant halt
}

runTests() {
  cd ${WORKSPACE}/RackHD/test
  RACKHD_TEST_LOGLVL=INFO python run.py --with-xunit 
  mkdir -p ${WORKSPACE}/xunit-reports
  cp *.xml ${WORKSPACE}/xunit-reports
}

waitForAPI() {
  timeout=0
  maxto=30
  url=http://localhost:9090/api/1.1/nodes
  while [ ${timeout} != ${maxto} ]; do
    wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 1 --continue ${url}
    if [ $? = 0 ]; then 
      break
    fi
    sleep 10
    timeout=`expr ${timeout} + 1`
  done
  if [ ${timeout} == ${maxto} ]; then
    echo "Timed out waiting for RackHD API service (duration=`expr $maxto \* 10`s)."
    exit 1
  fi
}

# Prepare the latest dependent repos to be shared with vagrant
prepareDeps

# Power off nodes and shutdown vagrant box
vagrantDestroy
nodesOff

# Power on vagrant box and nodes 
vagrantUp
waitForAPI
nodesOn

# Run tests
runTests

