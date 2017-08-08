#!/bin/bash

execWithTimeout() {
    set +e
    # $1 command to execute
    # $2 timeout
    # $3 retries on timeout
    if [ -z "${1}" ]; then
        echo "execWithTimeout() Command not specified"
        exit 2
    fi
    local cmd="/bin/sh -c \"$1\""
    #timeout default to 90 seconds
    local timeout=90
    local retry=3
    local result=0
    if [ ! -z "${2}" ]; then
        timeout=$2
    fi
    if [ ! -z "${3}" ]; then
        retry=$3
    fi
    echo "execWithTimeout() retry count is $retry"
    echo "execWithTimeout() timeout is set to $timeout"
    dir=${WORKSPACE}/build-config/deployment
    local time_cmd="${dir}/timeout_cmd.exp"
    if [ ! -x ${time_cmd} ]; then
        chmod a+x ${time_cmd}
        echo "chmod +x ${time_cmd}"
    fi

    i=1
    while [[ $i -le $retry ]]
    do
        ${time_cmd} "${timeout}" "${cmd}"
        result=$?
        echo "execWithTimeout() exit code $result"
        if [ $result = 0 ] ; then
            break
        fi
        ((i = i + 1))
    done
    if [ $result = 1 ] ; then
        echo "execWithTimeout() command timed out $retry times after $timeout seconds"
        exit 1
    elif [ $result != 0 ]; then
        echo "execWithTimeout() exit final code $result"
        exit $result
    fi
    set -e
}
####################################3
#
# To Check if a Shell Variable or Env Variable is empty or null (Jenkins Parameter but not set)
#
# $1; the variable name
#
# return 0: not empty
# return 1: empty or null
###################################
check_empty_variable(){
    if [ -n "$1" ] ; then
          # ${!1} will dereference the variable value
          if [ "${!1}" == "" ] || [ "${!1}" == "null" ]; then
              echo "[Error] Env Variable $1 is missing "
              return 1
          fi
    else
          echo "[Warning] Wrong usage of $0"
    fi
    return 0
}


