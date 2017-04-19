#!/bin/bash -ex
export VCOMPUTE=("${NODE_NAME}-Rinjin1","${NODE_NAME}-Rinjin2","${NODE_NAME}-Quanta")
REPOS=("on-http" "on-taskgraph" "on-dhcp-proxy" "on-tftp" "on-syslog")

HTTP_STATIC_FILES="${HTTP_STATIC_FILES}"
TFTP_STATIC_FILES="${TFTP_STATIC_FILES}"
MANIFEST_FILE="${MANIFEST_FILE}"

if [ ! -z "${1}" ]; then
  HTTP_STATIC_FILES=$1
fi
if [ ! -z "${2}" ]; then
  TFTP_STATIC_FILES=$2
fi
SKIP_PREP_DEP="${SKIP_PREP_DEP}"
if [ ! -z "${3}" ]; then
  SKIP_PREP_DEP=$3
fi

dlHttpFiles() {
  dir=${WORKSPACE}/build-deps/on-http/static/http/common
  mkdir -p ${dir} && cd ${dir}
  if [ -n "${INTERNAL_HTTP_ZIP_FILE_URL}" ]; then
    # use INTERNAL TEMP SOURCE
    wget -c -t 5 ${INTERNAL_HTTP_ZIP_FILE_URL} 
    unzip common.zip && mv common/* . && rm -rf common
  else
    # pull down index from bintray repo and parse files from index
    wget --no-check-certificate https://dl.bintray.com/rackhd/binary/builds/ && \
        exec  cat index.html |grep -o href=.*\"|sed 's/href=//' | sed 's/"//g' > files
    for i in `cat ./files`; do
      wget --no-check-certificate https://dl.bintray.com/rackhd/binary/builds/${i}
    done
    # attempt to pull down user specified static files
    for i in ${HTTP_STATIC_FILES}; do
      wget --no-check-certificate https://bintray.com/artifact/download/rackhd/binary/builds/${i}
    done
  fi
}

dlTftpFiles() {
  dir=${WORKSPACE}/build-deps/on-tftp/static/tftp
  mkdir -p ${dir} && cd ${dir}
  if [ -n "${INTERNAL_TFTP_ZIP_FILE_URL}" ]; then
    # use INTERNAL TEMP SOURCE
    wget -c -t 5 ${INTERNAL_TFTP_ZIP_FILE_URL} 
    unzip pxe.zip && mv pxe/* . && rm -rf pxe pxe.zip
  else
    # pull down index from bintray repo and parse files from index
    wget --no-check-certificate https://dl.bintray.com/rackhd/binary/ipxe/ && \
        exec  cat index.html |grep -o href=.*\"|sed 's/href=//' | sed 's/"//g' > files
    for i in `cat ./files`; do
      wget --no-check-certificate https://dl.bintray.com/rackhd/binary/ipxe/${i}
    done
    # attempt to pull down user specified static files
    for i in ${TFTP_STATIC_FILES}; do
      wget --no-check-certificate https://bintray.com/artifact/download/rackhd/binary/ipxe/${i}
    done
  fi
}

preparePackages() {
    pushd ${WORKSPACE}
    ./on-build-config/build-release-tools/HWIMO-BUILD ./on-build-config/build-release-tools/application/reprove.py \
    --manifest ${MANIFEST_FILE} \
    --builddir ${WORKSPACE}/build-deps \
    --jobs 8 \
    --force \
    checkout \
    packagerefs

    for i in ${REPOS[@]}; do
        pushd ${WORKSPACE}/build-deps/${i}
        npm install --production
        popd
    done

    cp -r build-deps/RackHD .
    if [ -d "build-deps/on-build-config" ]; then
        cp -r build-deps/on-build-config build-config
    else
        cp -r on-build-config build-config
    fi
    pushd build-config
    ./build-config
    popd

    popd
}

prepareDeps(){
  preparePackages
  dlTftpFiles
  dlHttpFiles
}

VCOMPUTE="${VCOMPUTE}"
if [ -z "${VCOMPUTE}" ]; then
  VCOMPUTE=("jvm-Quanta_T41-1" "jvm-vRinjin-1" "jvm-vRinjin-2")
fi


nodesDelete() {
  cd ${WORKSPACE}/build-config/deployment/
  if [ "${USE_VCOMPUTE}" != "false" ]; then
    for i in ${VCOMPUTE[@]}; do
      ./vm_control.sh "${ESXI_HOST},${ESXI_USER},${ESXI_PASS},delete,1,${i}_*"
    done
  fi
}

if [ "$SKIP_PREP_DEP" == false ] ; then
  # Prepare the latest dependent repos to be shared with vagrant
  prepareDeps
  nodesDelete
fi

