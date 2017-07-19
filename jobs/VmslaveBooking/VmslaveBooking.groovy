node{
    withCredentials([
    usernamePassword(credentialsId: 'ESXI_CREDS',
                        passwordVariable: 'ESXI_PASS',
                        usernameVariable: 'ESXI_USER')
    ]) {
        def bookings_requests = [:]
        def VMSLAVES="${VMSLAVES}"
        List vmslaves = VMSLAVES.split(',')
        for(vmslave in vmslaves){
            def label = vmslave
            bookings_requests[label] = {
                node(label) {
                    env.VM_NAME = label
                    deleteDir()
                    checkout scm
                    sh '''#!/bin/bash
                    cd $WORKSPACE/deployment
                    case $BOOKORCANCEL in
                        "true") action="snapshot_create";;
                        "false") action="snapshot_revert";;
                    esac
                    ./vm_control.sh "${ESXI_HOST},${ESXI_USER},${ESXI_PASS},$action,1,${VM_NAME}"
                    '''
                }
            }
        }
        parallel bookings_requests
    }
}