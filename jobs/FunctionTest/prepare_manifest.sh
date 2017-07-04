#!/bin/bash -ex
REPOS=("on-http" "on-taskgraph" "on-dhcp-proxy" "on-tftp" "on-syslog")
if (echo ${REPOS_UNDER_TEST} | grep -q  "image-service"); then
    REPOS+=("image-service")
fi
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

########################################
wget_download(){
  argv=($@)
  argc=$#
  retry_time=5
  remote_file=${argv[$(($argc -1 ))]} # not accurate enough..
  echo "[Info] Downloading ${remote_file}"

  # -c  resume getting a partially-downloaded file.
  # -nv reduce the verbose output
  # -t 5  the retry counter
  wget -c -t ${retry_time} -nv $@  # $@ means all function arguments from $1 to $n

  if [ $? -ne 0 ]; then
     echo "[Error]: wget download failed: ${remote_file}"
     exit 2
  else
     echo "[Info] wget download successfully ${remote_file}"
  fi
  local_file=${remote_file##*/}
  if [[ $remote_file == *zip* ]]; then
      echo "[Info] Checking zip file integrity for ${remote_file}"
      unzip -t $local_file
      if [ $? -ne 0 ]; then
          echo "[Error] the download file(${remote_file}) is incompleted !"
          exit 3
      fi
  fi

}

dlCommonFiles() {
    dir=$1
    mkdir -p ${dir} && cd ${dir}
    if [ -n "${INTERNAL_HTTP_ZIP_FILE_URL}" ]; then
        # use INTERNAL TEMP SOURCE
        wget_download ${INTERNAL_HTTP_ZIP_FILE_URL}

        unzip common.zip && mv common/* . && rm -rf common
    else
        # pull down index from bintray repo and parse files from index
        wget_download --no-check-certificate https://dl.bintray.com/rackhd/binary/builds/ && \
            exec  cat index.html |grep -o href=.*\"|sed 's/href=//' | sed 's/"//g' > files
        for i in `cat ./files`; do
            wget_download --no-check-certificate https://dl.bintray.com/rackhd/binary/builds/${i}
        done
        # attempt to pull down user specified static files
        for i in ${HTTP_STATIC_FILES}; do
            wget_download --no-check-certificate https://bintray.com/artifact/download/rackhd/binary/builds/${i}
        done
    fi
}

dlHttpFiles() {
    dir=${WORKSPACE}/build-deps/on-http/static/http/common
    dlCommonFiles ${dir}
}

dlImageServiceCommonFiles() {
    dir=${WORKSPACE}/build-deps/image-service/static/common
    dlCommonFiles ${dir}
}

dlTftpFiles() {
  dir=${WORKSPACE}/build-deps/on-tftp/static/tftp
  mkdir -p ${dir} && cd ${dir}
  if [ -n "${INTERNAL_TFTP_ZIP_FILE_URL}" ]; then
    # use INTERNAL TEMP SOURCE
    wget_download ${INTERNAL_TFTP_ZIP_FILE_URL}
    unzip pxe.zip && mv pxe/* . && rm -rf pxe pxe.zip
  else
    # pull down index from bintray repo and parse files from index
    wget_download --no-check-certificate https://dl.bintray.com/rackhd/binary/ipxe/ && \
        exec  cat index.html |grep -o href=.*\"|sed 's/href=//' | sed 's/"//g' > files
    for i in `cat ./files`; do
      wget_download --no-check-certificate https://dl.bintray.com/rackhd/binary/ipxe/${i}
    done
    # attempt to pull down user specified static files
    for i in ${TFTP_STATIC_FILES}; do
      wget_download --no-check-certificate https://bintray.com/artifact/download/rackhd/binary/ipxe/${i}
    done
  fi
}

preparePackages() {
    pushd ${WORKSPACE}
    ./build-config/build-release-tools/HWIMO-BUILD ./build-config/build-release-tools/application/reprove.py \
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
        # on-build-config from manifest has high priority
        cp -r build-deps/on-build-config build-config
    fi
    popd
}

prepareDeps(){
  preparePackages
  dlTftpFiles
  dlHttpFiles
  if (echo ${REPOS_UNDER_TEST} | grep -q "image-service"); then
      dlImageServiceCommonFiles
  fi
}

if [ "$SKIP_PREP_DEP" == false ] ; then
  # Prepare the latest dependent repos to be shared with vagrant
  prepareDeps
fi
