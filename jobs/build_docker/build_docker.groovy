node(build_docker_node){
    lock("docker"){
        timestamps{ 
            withEnv([
                "MANIFEST_FILE_URL=${env.MANIFEST_FILE_URL}",
                "IS_OFFICIAL_RELEASE=${env.IS_OFFICIAL_RELEASE}",
                "CLONE_DIR=b"]){
                deleteDir()
                def current_workspace = pwd()
                def shareMethod
                dir("Build_Docker_JFiles"){
                    checkout scm
                    shareMethod = load("jobs/shareMethod.groovy")
                }
                def url = "https://github.com/RackHD/on-build-config.git"
                def branch = "master"
                def targetDir = "build-config"
                shareMethod.checkout(url, branch, targetDir)

                withCredentials([
                    usernamePassword(credentialsId: 'ff7ab8d2-e678-41ef-a46b-dd0e780030e1',
                                     passwordVariable: 'SUDO_PASSWORD',
                                     usernameVariable: 'SUDO_USER'),
                    usernameColonPassword(credentialsId: 'a94afe79-82f5-495a-877c-183567c51e0b', 
                                          variable: 'BINTRAY_CREDS')]){
                    timeout(90){
                        withEnv(["WORKSPACE=${current_workspace}"]){
                            sh './Build_Docker_JFiles/jobs/build_docker/build_docker.sh'
                        }
                    }
                }
                env.DOCKER_WORKSPACE="${current_workspace}"
            }
        }
    }
}

