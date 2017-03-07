node(build_debian_node){
    withEnv([
        "BINTRAY_SUBJECT=rackhd", 
        "BINTRAY_REPO=debian", 
        "BINTRAY_COMPONENT=main", 
        "BINTRAY_DISTRIBUTION=trusty", 
        "BINTRAY_ARCHITECTURE=amd64"]){
        deleteDir()
        dir("on-build-config"){
            checkout scm
        }
        dir("DEBIAN"){
            unstash "debians"
        }
        withCredentials([
            usernameColonPassword(credentialsId: 'a94afe79-82f5-495a-877c-183567c51e0b', 
                                  variable: 'BINTRAY_CREDS')]){
            sh './on-build-config/jobs/release/release_debian.sh'
        }
    }
}

