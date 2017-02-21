node(build_vagrant_node){ws{
    def shareMethod
    dir("Release_Vagrant_JFiles"){
        checkout scm
        shareMethod = load("jobs/shareMethod.groovy")
    }
    def url = "https://github.com/RackHD/on-build-config.git"
    def branch = "*/master"
    def targetDir = "on-build-config"
    shareMethod.checkout(url, branch, targetDir)
    dir("VAGRANT"){
        unstash "vagrant"
    }
    withCredentials([
        usernameColonPassword(credentialsId: 'Atlas_User_Token', 
                              variable: 'ATLAS_CREDS')]) {
        sh './Release_Vagrant_JFiles/jobs/release/release_vagrant.sh'
    }   
}}
