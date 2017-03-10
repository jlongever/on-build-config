node(build_vagrant_node){ws{
    deleteDir()
    dir("on-build-config"){
        checkout scm
    }
    dir("VAGRANT"){
        unstash "vagrant"
    }
    withCredentials([
        usernameColonPassword(credentialsId: 'Atlas_User_Token', 
                              variable: 'ATLAS_CREDS')]) {
        sh './on-build-config/jobs/release/release_vagrant.sh'
    }   
}}
