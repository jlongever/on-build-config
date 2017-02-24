#!/bin/bash

############################################
# Post-Test scripts for ova, vagrantBox and docker.
# This script will up/deploy ova, box and docker images,
# Then check if RackHD services are good running.
#
# Usage: 
# post_test.sh \
# --type ova, vagrant or docker
#
# ova-post-test need some special parameter of net config and target esxi server
# --adminIP ***.***.***.***
# --adminGateway ***.***.***.***
# --adminNetmask 255.255.255.0
# --adminDNS ***.***.***.***
# --net "ADMIN"="External Connection"
# --datastore some-datastore
# --deployName ova-for-post-test
# --ovaFile /someDir/some.ova
# --vcenterHost ***.***.***.***
# --ntName user
# --ntPass password
# --esxiHost ***.***.***.***
#
# vagrant-post-test need some special parameter of boxFile and controlNetwork name
# --boxFile ./someDir/some.box
# --controlNetwork vmnet*
# --vagrantfile ./someFile
#
# docker-post-test need some special parameter of docker build record file and cloned RackHD repo
# --RackHDDir ./someDir/RackHD
# --buildRecord ./record_file
# A recorde_file contains repo:tag of all rackhd repos which build in one docker build, its format is like this:
# repo1:tag1 repo2:tag2 ......
# If build twice in one docker build job, the repos:tags of each build will be stored in each line
############################################

set -e

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
        # Note: the "ova-post-test" is defined locally on Jenkins slave's ansible host file.
        api_test_result=`ansible ova-for-post-test -a "wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 1 --continue ${url}"`
        echo $api_test_result | grep "$service_normal_sentence" > /dev/null  2>&1
        echo "[Debug] OVA ansible returns: $api_test_result"
        if [ $? = 0 ]; then  # FIXME: original code only treat "Authentication Failed" as single successful criteria, this only applies to when auth=disable.
           return 0
        else
           return -1
        fi
        ;;
      docker|vagrant)
        # NOTE : the '--waitretry' parameter doesn't work as expected for "Connection refused" error. so will have to do the retry outside this function.
        wget --retry-connrefused --waitretry=${waitretry} --read-timeout=20 --timeout=15 -t ${retry_cnt} --continue ${url} || ERR_RET=$?
        echo "[Debug] wget returns : $ERR_RET"
        if [ -z "$ERR_RET" ] || [ "$ERR_RET" == "6" ]; then     # 6 means: "Authentication Failed"
           return 0
        else
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
    case $type in
        ova)
        installed_version=`ansible ova-for-post-test -a "apt-cache policy rackhd" | grep Installed | awk '{print $2}'`
        ;;
        vagrant)
        installed_version=`vagrant ssh -c "apt-cache policy rackhd" | grep Installed | awk '{print $2}'`
        ;;
    esac
    if [ "$installed_version" != "$rackhdVersion" ]; then
        echo "Installed wrong rackhd version $installed_version"
        exit 1
    else
        echo "Installed correct rackhd version $installed_version"
    fi
}

############################################
# ova post test
############################################

deploy_ova() {
    echo yes | ovftool \
    --prop:adminIP=$adminIP  --prop:adminGateway=$adminGateway --prop:adminNetmask=$adminNetmask  --prop:adminDNS=$adminDNS \
    --overwrite --powerOffTarget --powerOn --skipManifestCheck \
    --net:"$net" \
    --datastore=$datastore \
    --name=$deployName \
    ${ovaFile} \
    vi://${ntName}:${ntPass}@${vcenterHost}/Infrastructure@onrack.cn/host/${esxiHost}/
    ssh-keygen -f "$HOME/.ssh/known_hosts" -R $adminIP
}

delete_ova() {
	ansible esxi -a "./vm_operation.sh -a delete ${esxiHost} 1 $deployName"
    if [ $? = 0 ]; then
      echo "Delete $deployName successfully!"
    fi
}

post_test_ova() {
    delete_ova
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
    docker stop $(docker ps -a -q)
    docker rm $(docker ps -a -q)
}

post_test_docker() {
    clean_all_containers
    cd $RackHDDir/docker 
    #if clone file name is not repo name, this scirpt should be edited.
    while read -r LINE; do
        cp docker-compose-mini.yml docker-compose-mini.yml.bak
        for repo_tag in $LINE; do
            repo=${repo_tag%:*}
            sed -i "s#rackhd/${repo}.*#rackhd/${repo_tag}#g" docker-compose-mini.yml
        done
        docker-compose -f docker-compose-mini.yml pull --ignore-pull-failures
        docker-compose -f docker-compose-mini.yml up -d
        mv docker-compose-mini.yml.bak docker-compose-mini.yml
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
