node('vmslave-config') {
    deleteDir()
    checkout scm
    stage("Update ansible hosts"){
        load("vmslave-config/pipeline/hosts_update/hosts_update.groovy")
    }
    stage("Config slaves"){
        load("vmslave-config/pipeline/vmslave_config/vmslave_config.groovy")
    }
}