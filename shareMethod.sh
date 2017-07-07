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
    i=1
    while [[ $i -le $retry ]]
    do
        expect -c "set timeout $timeout; spawn -noecho $cmd; expect timeout { exit 1 } eof { exit 0 }"
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
    fi
    set -e
}


