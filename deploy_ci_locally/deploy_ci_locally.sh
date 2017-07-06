#!/bin/bash -e
#############################################
#
# Global Variable
############################################
RACKHD_DOCKER_NAME="my/test"
API_PACKAGE_LIST="on-http-api2.0 on-http-redfish-1.0"
BASE_IMAGE_URL=http://rackhdci.lss.emc.com/job/Docker_Image_Build/lastSuccessfulBuild/artifact/rackhd_pipeline_docker.tar  # EMC internal Jenkins

#########################################
#
#  Usage
#
#########################################
USAGE(){
    echo "Function: this script is used to deploy RackHD within docker and prepare FIT environment"
    echo "Usage: $0 deploy|cleanUp [OPTION]"
    echo "  OPTION:"
    echo "    Mandatory Options:"
    echo "      -w, --WORKSPACE: The directory of workspace( where the code will be cloned to and staging folder), it's required"
    echo "      -p, --SUDO_PASSWORD: password of current user which has sudo privilege, it's required."
    echo "    Optional Options:"
    echo "      -s, --SRC_CODE_DIR: The directory of source code which contains all the repositories of RackHD"
    echo "                       If it's not provided, the script will clone the latest source code under $WORKSPACE/build-deps"
    echo "      -f, --MANIFEST_FILE: The path of manifest file"
    echo "                       If it's not provided, the script will generate a new manifest with latest commit of repositories of RackHD"
    echo "      -b, --BUILD_CONFIG_DIR: The directory of repository on-build-config"
    echo "                       If it's not provided, the script will clone the latest repository on-build-config under $WORKSPACE"
    echo "      -r, --RACKHD_DIR: The directory of repository RackHD"
    echo "                       If it's not provided, the script will clone the latest repository RackHD under $WORKSPACE"
    echo "      -i, --RACKHD_IMAGE_PATH: The path of base docker image of rackhd CI test (rackhd/pipeline)"
    echo "                       If it's not provided, the script will download the image from jenkins artifacts"
    echo "      -m, --MODIFY_API_PACKAGE: Default value is false. If true, reinstall packages: on-http-api2.0 on-http-redfish-1.0"
    echo "      -h, --help : Give this help list"
}


##############################################
#
# Remove docker images after test
#
###########################################

cleanUpDockerImages(){
    set +e
    local to_be_removed="$(echo $SUDO_PASSWORD |sudo -S docker images ${RACKHD_DOCKER_NAME} -q)  \
                         $(echo $SUDO_PASSWORD |sudo -S docker images rackhd/pipeline -q)  \
                         $(echo $SUDO_PASSWORD |sudo -S docker images -f "dangling=true" -q )"
    # remove ${RACKHD_DOCKER_NAME} image,  rackhd/pipeline image and <none>:<none> images
    if [ ! -z "${to_be_removed// }" ] ; then
         echo $SUDO_PASSWORD |sudo -S docker rmi $to_be_removed
    fi
    set -e
}
##############################################
#
# Remove docker instance which are running
#
###########################################
cleanUpDockerContainer(){
    set +e
    local docker_name_key=$1
    local running_docker=$(echo $SUDO_PASSWORD |sudo -S docker ps -a |grep "$1" |awk '{print $1}')
    if [ "$running_docker" != "" ]; then
         echo $SUDO_PASSWORD |sudo -S docker stop $running_docker
         echo $SUDO_PASSWORD |sudo -S docker rm   $running_docker
    fi
    set -e
}

######################################
#
# Clean Up runnning docker instance
#
#####################################
cleanupDockers(){
    echo "CleanUp Dockers ..."
    set +e
    cleanUpDockerContainer "${RACKHD_DOCKER_NAME}"
    cleanUpDockerImages
    set -e
}


#########################################
#
# Start Host services to avoid noise
#
#######################################
startServices(){
    echo "Start Services (mongo/rabbitmq)..."
    set +e
    mongo_path=$( which mongod )
    rabbitmq_path=$( which rabbitmq-server )
    if [ ! -z "$mongo_path" ]; then
        echo $SUDO_PASSWORD |sudo -S service mongodb start
    fi
    if [ ! -z "$rabbitmq_path" ]; then
        echo $SUDO_PASSWORD |sudo -S service rabbitmq-server start
    fi
    set -e
}
#########################################
#
# Stop Host services to avoid noise, there're mongo/rabbitmq inside docker , port confliction with OS's mongo/rabbitmq will occur.
#
#######################################
stopServices(){
    echo "Stop Services (mongo/rabbitmq)..."
    set +e
    netstat -ntlp |grep ":27017 "
    mongo_port_in_use=$?
    netstat -ntlp |grep ":5672 "
    rabbitmq_port_in_use=$?
    if [ "$mongo_port_in_use" == "0" ]; then
        echo $SUDO_PASSWORD |sudo -S service mongodb stop
    fi
    if [ "$rabbitmq_port_in_use" == "0" ]; then
        echo $SUDO_PASSWORD |sudo -S service rabbitmq-server stop
    fi
    set -e
}

############################################
#
# Clean Up if you want to stop RackHD docker and recover services
#
###########################################
cleanUp(){
    set +e
    echo "*****************************************************************************************************"
    echo "Start to clean up environment: stopping running containers, starting service mongodb and rabbitmq-server"
    echo "*****************************************************************************************************"
    cleanupDockers
    startServices
    netstat -ntlp
    set -e
    echo "*****************************************************************************************************"
    echo "End to clean up environment: stopping running containers, starting service mongodb and rabbitmq-server"
    echo "*****************************************************************************************************"
}


##############################################
# Clean up previous dirty space before everyting starts
#
#############################################
prepareEnv(){
    echo "*****************************************************************************************************"
    echo "Start to clean up environment: stopping running containers, service mongodb and rabbitmq-server"
    echo "*****************************************************************************************************"
    cleanupDockers
    stopServices
    #############################################
    #
    # Default Parameter Checking
    #
    #############################################
    if [ ! -n "${WORKSPACE}" ]; then
        echo "Arguments WORKSPACE is required"
        exit 1
    else
        if [ ! -d "${WORKSPACE}" ]; then
            mkdir -p ${WORKSPACE}
        fi
    fi
    if [ ! -n "${BUILD_CONFIG_DIR}" ]; then
        pushd $WORKSPACE
        rm -rf on-build-config
        git clone https://github.com/RackHD/on-build-config
        BUILD_CONFIG_DIR=$WORKSPACE/on-build-config
        popd
    fi
    if [ ! -n "${RACKHD_DIR}" ]; then
        pushd $WORKSPACE
        rm -rf RackHD
        git clone https://github.com/RackHD/RackHD
        RACKHD_DIR=$WORKSPACE/RackHD
        popd
    fi
    if [ ! -n "${RACKHD_IMAGE_PATH}" ]; then
        pushd $WORKSPACE
        # Auto Select the best available server to download
        set +e 
        ping -q -c 1 rackhdci.lss.emc.com > /dev/null
        if [ "$?" != "0" ]; then
           BASE_IMAGE_URL=http://147.178.202.18/job/Docker_Image_Build/lastSuccessfulBuild/artifact/rackhd_pipeline_docker.tar  # the cloud Jenkins mirror
        fi
        set -e
        download_docker_file=$( echo ${BASE_IMAGE_URL##*/} )
        rm -rf   $download_docker_file
        wget $BASE_IMAGE_URL
        RACKHD_IMAGE_PATH=$WORKSPACE/$download_docker_file
        popd
    fi
    if [ ! -n "${MODIFY_API_PACKAGE}" ]; then
        MODIFY_API_PACKAGE=false
    fi
    if [ ! -n "${SRC_CODE_DIR}" ]; then
        if [ ! -n "${MANIFEST_FILE}" ]; then
           # Checkout RackHD source code and build them
           generateManifest # it will generate a manifest file and export the MANIFEST_FILE variable
        fi
        preparePackages $MANIFEST_FILE # it will clone and build RackHD code under ${WORKSPACE}/build-deps according to the new_manifest
        SRC_CODE_DIR=${WORKSPACE}/build-deps
    fi
    echo "*****************************************************************************************************"
    echo "End to clean up environment: stopping running containers, service mongodb and rabbitmq-server"
    echo "*****************************************************************************************************"
}

waitForAPI() {
  echo "*****************************************************************************************************"
  echo "Try to access the RackHD API"
  echo "*****************************************************************************************************"
  timeout=0
  maxto=60
  set +e
  url=http://localhost:9090/api/2.0/nodes #9090 is the rackhd api port which docker uses
  while [ ${timeout} != ${maxto} ]; do
    wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 1 --continue ${url}
    if [ $? = 0 ]; then
      break
    fi
    sleep 10
    timeout=`expr ${timeout} + 1`
  done
  set -e
  if [ ${timeout} == ${maxto} ]; then
    echo "Timed out waiting for RackHD API service (duration=`expr $maxto \* 10`s)."
    exit 1
  fi
  echo "*****************************************************************************************************"
  echo "RackHD API is accessable"
  echo "*****************************************************************************************************"
}

generateManifest(){
    echo "*****************************************************************************************************"
    echo "Start to generate a manifest with the latest commit of RackHD" 
    echo "*****************************************************************************************************"
    pushd $BUILD_CONFIG_DIR
    # Generate a manifest file
    ./build-release-tools/HWIMO-BUILD build-release-tools/application/generate_manifest.py \
    --branch master \
    --date current \
    --timezone -0500 \
    --builddir $WORKSPACE/build-deps \
    --dest-manifest new_manifest \
    --force \
    --jobs 8
    # above script will generate a manifest file as $WORKSPACE/new_manifest
    MANIFEST_FILE=$WORKSPACE/new_manifest
    rm -rf $WORKSPACE/build-deps
    popd
    echo "*****************************************************************************************************"
    echo "End to generate manifest file"
    echo "*****************************************************************************************************"
}
preparePackages() {
    echo "*****************************************************************************************************"
    echo "Start to check out RackHD source code and run npm build"
    echo "*****************************************************************************************************"
    pushd $BUILD_CONFIG_DIR
    pwd
    export SKIP_PREP_DEP=false
    export MANIFEST_FILE=$MANIFEST_FILE
    export WORKSPACE=$WORKSPACE
    ln -s $BUILD_CONFIG_DIR $WORKSPACE/build-config
    bash jobs/FunctionTest/prepare_manifest.sh
    popd
    echo "*****************************************************************************************************"
    echo "End to check out RackHD source code and run npm build"
    echo "*****************************************************************************************************"
}

apiPackageModify() {
    pushd ${SRC_CODE_DIR}/on-http/extra
    sed -i "s/.*git symbolic-ref.*/ continue/g" make-deb.sh
    sed -i "/build-package.bash/d" make-deb.sh
    sed -i "/GITCOMMITDATE/d" make-deb.sh
    sed -i "/mkdir/d" make-deb.sh
    bash make-deb.sh
    popd
    for package in ${API_PACKAGE_LIST}; do
      echo $SUDO_PASSWORD |sudo -S pip uninstall -y ${package//./-} || true
      pushd ${SRC_CODE_DIR}/on-http/$package
        fail=true
        while $fail; do
          python setup.py install
          if [ $? -eq 0 ];then
              fail=false
          fi
        done
      popd
    done
}
###################################
#
# Modify the RackHD default Config file
#
#################################

setupRackHDConfig(){
    echo "*****************************************************************************************************"
    echo "Customize RackHD Config Files to adopt RackHD docker enviroment"
    echo "*****************************************************************************************************"

    RACKHD_DHCP_HOST_IP=$(ifconfig | awk '/inet addr/{print substr($2,6)}' |grep 172.31.128)
    sed -i "s/172.31.128.1/${RACKHD_DHCP_HOST_IP}/g" ${BUILD_CONFIG_DIR}/jobs/pr_gate/docker/monorail/config.json
}

###################################
#
# Modify the FIT Test Config files
#
#################################
setupTestsConfig(){
    echo "*****************************************************************************************************"
    echo "Customize FIT Config Files to adopt RackHD docker enviroment"
    echo "*****************************************************************************************************"

    RACKHD_DHCP_HOST_IP=$(ifconfig | awk '/inet addr/{print substr($2,6)}' |grep 172.31.128)

    pushd ${RACKHD_DIR}/test/config
    sed -i "s/\"username\": \"vagrant\"/\"username\": \"${USER}\"/g" credentials_default.json
    sed -i "s/\"password\": \"vagrant\"/\"password\": \"${SUDO_PASSWORD}\"/g" credentials_default.json
    popd

    pushd ${RACKHD_DIR}
    find ./ -type f -exec sed -i -e "s/172.31.128.1/${RACKHD_DHCP_HOST_IP}/g" {} \;
    #FIXME, only FIT config file should be replace , once FIT code being ready( https://rackhd.atlassian.net/browse/RAC-5418 ).
    popd
}

dockerUp(){
    echo "*****************************************************************************************************"
    echo "Start to build and run RackHD CI docker"
    echo "*****************************************************************************************************"
    echo $SUDO_PASSWORD |sudo -S docker load -i $RACKHD_IMAGE_PATH
    pushd $BUILD_CONFIG_DIR/deploy_ci_locally
    cp -r $BUILD_CONFIG_DIR/jobs/pr_gate/docker/rackhd.yml .
    # Build docker image which contains RackHD
    echo $SUDO_PASSWORD |sudo -S docker build -t my/test .
    echo $SUDO_PASSWORD |sudo -S docker run --net=host -v /etc/localtime:/etc/localtime:ro -v ${SRC_CODE_DIR}/:/RackHD -v ${BUILD_CONFIG_DIR}/jobs/pr_gate/docker/monorail/:/opt/monorail -d -t my/test
    popd
    echo "*****************************************************************************************************"
    echo "End to build and run RackHD CI docker"
    echo "*****************************************************************************************************"
}

deployTestEnv(){
    echo "*****************************************************************************************************"
    echo "Start to create the virtualenv for RackHD/test"
    echo "*****************************************************************************************************"
    pushd ${RACKHD_DIR}/test
    ./mkenv.sh on-build-config
    popd
    echo "*****************************************************************************************************"
    echo "End to create the virtualenv for RackHD/test"
    echo "*****************************************************************************************************"
}

deployRackHD(){
    # Checkout tools: on-build-config and RackHD
    prepareEnv
    if $MODIFY_API_PACKAGE;then
        apiPackageModify
    fi
    # Build docker image with the built RackHD and updated config file
    # Run the built docker image
    setupRackHDConfig
    dockerUp
    # Check the RackHD API is accessable
    waitForAPI   

}

prepareFIT(){
    # Update config of RackHD according to the env:
    # such as: replacing 172.31.128.1 with the actual ip of NIC whose ip starts with 172.31.128
    setupTestsConfig

    # Create the virtualenv for test
    deployTestEnv

    echo "*****************************************************************************************************"
    echo "RackHD & FIT are ready now. you can run FIT like below example (NOTE: Please use -stack docker_local_run )"
    echo ""
    echo "$ python run_tests.py -test tests -group smoke -stack docker_local_run --sm-amqp-use-user guest -v 4 -xunit"
    echo ""
    echo "More FIT usage , please refer to https://github.com/RackHD/RackHD/blob/master/test/README.md"
    echo "*****************************************************************************************************"



}


###################################################################
#
#  Main
#
##################################################################
parseArguments(){

    while [ "$1" != "" ]; do
        case $1 in
            -w | --WORKSPACE )              shift
                                            WORKSPACE=$1
                                            ;;
            -s | --SRC_CODE_DIR )           shift
                                            SRC_CODE_DIR=$1
                                            ;;
            -f | --MANIFEST_FILE )          shift
                                            MANIFEST_FILE=$1
                                            ;;
            -b | --BUILD_CONFIG_DIR )       shift
                                            BUILD_CONFIG_DIR=$1
                                            ;;
            -r | --RACKHD_DIR )             shift
                                            RACKHD_DIR=$1
                                            ;;
            -i | --RACKHD_IMAGE_PATH )      shift
                                            RACKHD_IMAGE_PATH=$1
                                            ;;
            -m | --MODIFY_API_PACKAGE )     shift
                                            MODIFY_API_PACKAGE=$1
                                            ;;
            -p | --SUDO_PASSWORD )          shift
                                            SUDO_PASSWORD=$1
                                            ;;
            -h | --help )                   USAGE
                                            exit
                                            ;;
            * )                             USAGE
                                            exit 1
        esac
        shift
    done

}

case "$1" in
  cleanUp)
      shift
      parseArguments $@
      cleanUp
  ;;

  deploy)
      shift
      parseArguments $@
      deployRackHD
      prepareFIT
  ;;

  *)
    USAGE
    exit 1
  ;;

esac
