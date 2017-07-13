node(build_debian_node){
    lock("debian"){
        withEnv([
            "MANIFEST_FILE_URL=${env.MANIFEST_FILE_URL}",
            "IS_OFFICIAL_RELEASE=${env.IS_OFFICIAL_RELEASE}",
            "ARTIFACTORY_URL=${env.ARTIFACTORY_URL}",
            "STAGE_REPO_NAME=${env.STAGE_REPO_NAME}",
            "BINTRAY_SUBJECT=${env.BINTRAY_SUBJECT}",
            "BINTRAY_REPO=debian",
            "DEB_COMPONENT=${env.DEB_COMPONENT}",
            "DEB_DISTRIBUTION=trusty",
            "DEB_ARCHITECTURE=amd64"]) {
            deleteDir()
            dir("on-build-config"){
                checkout scm
            }

            // credentials are binding to Jenkins Server
            withCredentials([
                usernamePassword(credentialsId: 'MN_ARTIFACTORY_CRED',
                                 passwordVariable: 'ARTIFACTORY_PWD',
                                 usernameVariable: 'ARTIFACTORY_USR'),

                usernameColonPassword(credentialsId: "ff7ab8d2-e678-41ef-a46b-dd0e780030e1", 
                                      variable: "SUDO_CREDS"),
                usernameColonPassword(credentialsId: "a94afe79-82f5-495a-877c-183567c51e0b", 
                                      variable:"BINTRAY_CREDS")]){
                sh './on-build-config/jobs/build_debian/build_debian.sh'
            }

            // inject properties file as environment variables
            if(fileExists ("downstream_file")) {
                def props = readProperties file: "downstream_file"
                if(props["RACKHD_VERSION"]) {
                   env.RACKHD_VERSION = "${props.RACKHD_VERSION}"
                }
                if(props["RACKHD_COMMIT"]) {
                    env.RACKHD_COMMIT = "${props.RACKHD_COMMIT}"
                }
            }
             
            archiveArtifacts 'b/**/*.deb, downstream_file'
            stash name: 'debians', includes: 'b/**/*.deb'
        }
    }
}
