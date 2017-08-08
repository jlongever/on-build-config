#!/bin/bash
############################################
# Post-Test scripts for ova, vagrantBox and docker.
# This script will up/deploy ova, box and docker images,
# Then check if RackHD services are good running.
#
# Usage: 
# post_test.sh \
# --type             ova, vagrant or docker
# --rackhdVersion    the desired RackHD version, it's to be compared with the actual install version.

#
#--------------------------------------------------
# 1.ova-post-test need some special parameter of net config and target esxi server
#
#  1.1) ova-post-test's case #1, if there's no DHCP for target vSphere/vCenter, then we need to specific a static IP, so that we can talk with the OVA
#   Parameter Group for Case #1
#   --adminIP ***.***.***.***
#   --adminGateway ***.***.***.***
#   --adminNetmask 255.255.255.0
#   --adminDNS ***.***.***.***
#   --net "ADMIN"="External Connection"
#   --datastore some-datastore
#   --deployName ova-for-post-test
#   --ovaFile /someDir/some.ova
#   --vcenterHost ***.***.***.***
#   --ntName user of vCenter
#   --ntPass password of vCenter
#   --esxiHostUser:  ESXi vsphere user name
#   --esxiHostPass:  ESXi vsphere password
#   --esxiHost ***.***.***.***
#
#  1.2) ova-post-test's case #2, if there's DHCP available for target vSphere, we don't need to specific target IP. but we need to wait for IP then retrieve it. so in this case, vSphere(ESXi) is enough.
#   Parameter Group for Case #2
#   --net "ADMIN"="External Connection"
#   --datastore some-datastore
#   --deployName ova-for-post-test
#   --ovaFile /someDir/some.ova
#   --esxiHostUser:  ESXi vsphere user name
#   --esxiHostPass:  ESXi vsphere password
#   --esxiHost ***.***.***.***
#--------------------------------------------------
#
# 2.vagrant-post-test need some special parameter of boxFile and controlNetwork name
# --boxFile ./someDir/some.box
# --controlNetwork vmnet*
# --vagrantfile ./someFile
#
#--------------------------------------------------

# 3.docker-post-test need some special parameter of docker build record file and cloned RackHD repo
# --RackHDDir ./someDir/RackHD
# --buildRecord ./record_file
# A recorde_file contains repo:tag of all rackhd repos which build in one docker build, its format is like this:
# repo1:tag1 repo2:tag2 ......
# If build twice in one docker build job, the repos:tags of each build will be stored in each line
############################################

set -e

#####################################
#
# the default OVA/Vagrant login user/password are both `vagrant`
# which was specified in https://github.com/RackHD/RackHD/blob/master/packer/http/preseed.cfg
#
####################################
rackhd_default_usr=vagrant
rackhd_default_pwd=vagrant



while [ "$1" != "" ];do
    case $1 in
        --type)
            shift
            type=$1;;
        --adminIP)
            shift
            adminIP=$1;;
        --adminGateway)
            shift
            adminGateway=$1;;
        --adminNetmask)
            shift
            adminNetmask=$1;;
        --adminDNS)
            shift
            adminDNS=$1;;
        --net)
            shift
            net=$1;;
        --datastore)
            shift
            datastore=$1;;
        --deployName)
            shift
            deployName=$1;;
        --ovaFile)
            shift
            ovaFile=$1;;
        --vcenterHost)
            shift
            vcenterHost=$1;;
        --ntName)
            shift
            ntName=$1;;
        --ntPass)
            shift
            ntPass=$1;;
        --esxiHost)
            shift
            esxiHost=$1;;
         --esxiHostUser)
            shift
            esxiHostUser=$1;;
        --esxiHostPass)
            shift
            esxiHostPass=$1;;
        --boxFile)
            shift
            boxFile=$1;;
        --controlNetwork)
            shift
            controlNetwork=$1;;
        --vagrantfile)
            shift
            vagrantfile=$1;;
        --RackHDDir)
            shift
            RackHDDir=$1;;
        --buildRecord)
            shift
            buildRecord=$1;;
        --rackhdVersion)
            shift
            rackhdVersion=$1;;
        *)
        echo "[Error]: Unknown Parameter =$1"
        exit 1
    esac
    shift
done

#################
# using wget to access RackHD API IP:port/api/2.0/nodes
################
findRackHDService() {
    local retry_cnt=${1:-1} # default 1 time retry
    local waitretry=${2:-1}  # default 1 time interval
    local url=${3:-localhost:8080/api/2.0/nodes}
    local ERR_RET=     # init it with undefined. otherwise, it will inherit old value of last run
    case $type in
      ova)
        service_normal_sentence="Authentication Failed"
        TMP_LOG_FILE=./tmp_check_rackhd_api.txt
        rm -f $TMP_LOG_FILE
        check_api_command="wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 1 --continue ${url}"
        sshpass -p ${rackhd_default_pwd} ssh ${rackhd_default_usr}@${adminIP}  -o StrictHostKeyChecking=no  ${check_api_command}  > $TMP_LOG_FILE 2>&1
        sed -i  "s/Warning: Permanently added.*//g" $TMP_LOG_FILE  # Remove the senstive IP info in the log.
        api_test_result=$(cat $TMP_LOG_FILE )
        rm -f $TMP_LOG_FILE # Clean Up
        echo $api_test_result | grep "$service_normal_sentence" > /dev/null  2>&1
        if [ $? = 0 ]; then  # FIXME: original code only treat "Authentication Failed" as single successful criteria, this only applies to when auth=disable.
           echo "[Debug] successful.        in this retry time: OVA ansible returns: $api_test_result"
           return 0
        else
           echo "[Debug] no luck this time. in this retry time: OVA ansible returns: $api_test_result"
           return -1
        fi
        ;;
      docker|vagrant)
        # NOTE : the '--waitretry' parameter doesn't work as expected for "Connection refused" error. so will have to do the retry outside this function.
        wget --retry-connrefused --waitretry=${waitretry} --read-timeout=20 --timeout=15 -t ${retry_cnt} --continue ${url} || ERR_RET=$?
        echo "[Debug] in this retry time: wget returns : $ERR_RET"
        if [ -z "$ERR_RET" ] || [ "$ERR_RET" == "6" ]; then     # 6 means: "Authentication Failed"
           echo "[Debug] successful retrieve rackhd API."
           return 0
        else
           echo "[Debug] failing retrieve rackhd API."
           return -1
        fi
        ;;
    esac
}

waitForAPI() {
    local flags=$-  # if use ```$(echo $-|grep e)```, the $- will run in a new shell session
    # retrive old flag
    if [ "$(echo $flags|grep e)" != "" ]; then
        e_flag=true 
    fi
    # set +e, to tolerate the failure during retry http://www.davidpashley.com/articles/writing-robust-shell-scripts/
    set +e

    local maxto=60
    local interval=10  # sleep second
    local timeout=0

    while [ ${timeout} != ${maxto} ]; do
        echo "try RackHD API .. elapse : `expr $timeout \* $interval`s"
        case $type in
          ova)
           # ova Northbound Port default to 8080, but it should be reached via ansible to OVA VM's IP
           findRackHDService 1 1  localhost:8080/api/2.0/nodes
           ;;
          docker)
           # FIXME, original code treats "Authentication Failed" is not acceptable for docker, is it correct ?
           findRackHDService 1 1  http://172.31.128.1:9080/api/2.0/nodes
           ;;
          vagrant)
           # ova Northbound Port default to 9090
           findRackHDService 1 1  localhost:9090/api/2.0/nodes
           ;;
        esac

        if [ $? = 0 ]; then
          echo "RackHD services perform normally! (total time = `expr $timeout \* $interval`s)."
          break
        fi
        sleep ${interval}
        timeout=`expr ${timeout} + 1`
    done

    # restore the "set -e" flag if was set
    if [ "$e_flag" == true ]; then
       set -e
    fi

    if [ ${timeout} == ${maxto} ]; then
        echo "Timed out waiting for RackHD API service (duration=`expr $maxto \* $interval`s)."
        exit 1
    fi



}



checkRackHDVersion() {

    if [ "$rackhdVersion" == "" ]; then
        echo "[Error] rackhdVersion parameter is blank, Abort!"
        exit 2
    fi

    # since Docker images are build from source code, so no way available to check RackHD version via deb package.
    case $type in
        ova)
            apt_cache=$( sshpass -p ${rackhd_default_pwd} ssh ${rackhd_default_usr}@${adminIP}  -o StrictHostKeyChecking=no   'apt-cache policy rackhd' )
            # above command will use SSH usr/pwd to remote execute shell command in adminIP
            # -o StrictHostKeyChecking=no will auto added the adminIP into known_host without asking.
            
            if [ $? != 0 ]; then
                echo "[Error] Ansible Error(ansible ova-for-post-test -a [apt-cache policy rackhd]), returns:  $apt_cache "
                exit 2
            fi
        ;;
        vagrant)
            apt_cache=$(vagrant ssh -c "apt-cache policy rackhd" )
            if [ $? != 0 ]; then
                echo "[Error] Vagrant SSH(vagrant ssh -c [apt-cache policy rackhd]) Error, returns:  $apt_cache "
                exit 2
            fi
        ;;
    esac
    echo "[Debug] RackHD installation candidates in remote apt cache as below : ------------START----------"
    echo "$apt_cache"
    echo "[Debug] RackHD installation candidates in remote apt cache as above ------------- END-----------"
    installed_version=$( echo "$apt_cache" | grep Installed | awk '{print $2}' )  # Tip: remember to use quote in echo "$apt_cache", to preserve line break
    echo "[Debug] installed_version=$installed_version"

    if [ "$installed_version" != "$rackhdVersion" ]; then
        echo "Installed wrong rackhd version $installed_version, desired version is $rackhdVersion"
        exit 1
    else
        echo "Installed correct rackhd version $installed_version"
    fi
}

############################################
# ova post test
############################################

deploy_ova() {
    if [ -n "${adminIP}" ]; then # if $adminIP not given, it means we are using vCenter pre-set IP deployment
        echo "[Info] Deploy OVA with Pre-Configured IP Address to vCenter. it's suitable for enviroment without DHCP."
        echo yes | ovftool \
        --prop:adminIP=$adminIP  --prop:adminGateway=$adminGateway --prop:adminNetmask=$adminNetmask  --prop:adminDNS=$adminDNS \
        --overwrite --powerOffTarget --powerOn --skipManifestCheck \
        --net:"$net" \
        --datastore=$datastore \
        --name=$deployName \
        ${ovaFile} \
        vi://${ntName}:${ntPass}@${vcenterHost}/Infrastructure@onrack.cn/host/${esxiHost}/
    else
        echo "[Info] Deploy OVA with DHCP , it's suitable for  enviroment with DHCP."
        TMP_FILE=tmp_ovf_result.txt
        rm -f ${TMP_FILE}
        echo yes | ovftool \
        --X:waitForIp \
        --overwrite --powerOffTarget --powerOn --skipManifestCheck \
        --net:"$net" \
        --datastore=$datastore \
        --name=$deployName \
        ${ovaFile} \
        vi://${esxiHostUser}:${esxiHostPass}@${esxiHost}/ > ${TMP_FILE}
        adminIP=$( grep "Received IP address:"   ${TMP_FILE} | awk '{print $7}') # with parameter 'waitForIp', the ovftool will dump in stdout like "Received IP address: 10.111.222.1"
        rm -f ${TMP_FILE} # Clean Up

    fi

    if [ $? = 0 ]; then
        echo "[Info] Deploy OVA successfully".
    else
        echo "[Error] Deploy OVA failed."
        exit 3
    fi
    ssh-keygen -f "$HOME/.ssh/known_hosts" -R $adminIP > /dev/null 2>&1  # to avoid IP exposing
}

delete_ova() {
    pushd ./build-config/deployment/
    ./vm_control.sh "${esxiHost},${esxiHostUser},${esxiHostPass},delete,1,$deployName"
    popd
    if [ $? = 0 ]; then
      echo "Delete $deployName successfully!"
    else
      echo "[Warning] the deployed OVA still lives on ESXi Host, it failed to be deleted automaticlly, please remove it manually."
    fi
}

post_test_ova() {
#    delete_ova  
#####################
# Remove "delete_ova" above .Because ovftool --overwrite --powerOffTarget will delete old VM with same name.
# ovftool will do the sync well by itself.
# otherwise, will encounter issue: "Power Off Virtual machines : The  object has already been deleted or has not been completely created"
####################
    deploy_ova
    waitForAPI
    checkRackHDVersion
    delete_ova
}

############################################
# vagrant post test
############################################

create_vagrant_file() {
    sed -e "s#rackhd/rackhd#${boxFile}#g" \
        -e '/target.vm.box_version/d' \
        -e "s#em1#${controlNetwork}#g" \
        $vagrantfile > Vagrantfile
}

post_test_vagrant() {
    create_vagrant_file
    vagrant destroy -f
    vagrant up --provision
    trap "vagrant destroy -f" SIGINT SIGTERM SIGKILL EXIT
    waitForAPI
    checkRackHDVersion
    vagrant destroy -f
}

############################################
# docker post test
############################################

clean_all_containers() {
    local containers=$(docker ps -a -q)
    if [ "$containers" != "" ]; then
        echo "Clean Up containers : " ${containers}
        docker stop ${containers}
        docker rm  ${containers}
    fi

}

post_test_docker() {
    clean_all_containers
    cd $RackHDDir/docker 
    #if clone file name is not repo name, this scirpt should be edited.
    while read -r LINE; do
        cp docker-compose.yml docker-compose.yml.bak
        for repo_tag in $LINE; do
            repo=${repo_tag%:*}
            sed -i "s#rackhd/${repo}.*#rackhd/${repo_tag}#g" docker-compose.yml
        done
        docker-compose -f docker-compose.yml up -d
        mv docker-compose.yml.bak docker-compose.yml
        waitForAPI
        clean_all_containers
    done < $buildRecord
}

############################################
# run post test
############################################
case $type in
    ova)
    post_test_ova
    ;;
    docker)
    post_test_docker
    ;;
    vagrant)
    post_test_vagrant 
    ;;
esac
