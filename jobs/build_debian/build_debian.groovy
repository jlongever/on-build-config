node(build_debian_node){
    lock("debian"){
        timestamps{
            withEnv([
                "MANIFEST_FILE_URL=${env.MANIFEST_FILE_URL}",
                "IS_OFFICIAL_RELEASE=${env.IS_OFFICIAL_RELEASE}",
                "BINTRAY_SUBJECT=rackhd-mirror",
                "CI_BINTRAY_REPO=debian",
                "BINTRAY_COMPONENT=main",
                "BINTRAY_DISTRIBUTION=trusty", 
                "BINTRAY_ARCHITECTURE=amd64"]) {
                deleteDir()
                def shareMethod
                dir("Build_Debian_JFiles"){
                    checkout scm
                    shareMethod = load("jobs/shareMethod.groovy")
                }
                def url = "https://github.com/RackHD/on-build-config.git"
                def branch = "*/master"
                def targetDir = "on-build-config"
                shareMethod.checkout(url, branch, targetDir)

                // credentials are binding to Jenkins Server
                withCredentials([
                    usernameColonPassword(credentialsId: "ff7ab8d2-e678-41ef-a46b-dd0e780030e1", 
                                          variable: "SUDO_CREDS"),
                    usernameColonPassword(credentialsId: "a94afe79-82f5-495a-877c-183567c51e0b", 
                                          variable:"BINTRAY_CREDS")]){
                    sh './Build_Debian_JFiles/jobs/build_debian/build_debian.sh'
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
}
