node(build_debian_node){
    withEnv([
        "BINTRAY_SUBJECT=rackhd", 
        "BINTRAY_REPO=debian", 
        "BINTRAY_COMPONENT=main", 
        "BINTRAY_DISTRIBUTION=trusty", 
        "BINTRAY_ARCHITECTURE=amd64"]){
        deleteDir()
        def shareMethod
        dir("Release_Debian_JFiles"){
            checkout scm
            shareMethod = load("jobs/shareMethod.groovy")
        }
        def url = "https://github.com/RackHD/on-build-config.git"
        def branch = "*/master"
        def targetDir = "on-build-config"
        shareMethod.checkout(url, branch, targetDir)
        dir("DEBIAN"){
            unstash "debians"
        }
        withCredentials([
            usernameColonPassword(credentialsId: 'a94afe79-82f5-495a-877c-183567c51e0b', 
                                  variable: 'BINTRAY_CREDS')]){
            sh './Release_Debian_JFiles/jobs/release/release_debian.sh'
        }
    }
}

