node(build_docker_node){
    withEnv([
        "MANIFEST_FILE_URL=${env.MANIFEST_FILE_URL}",
        "IS_OFFICIAL_RELEASE=${env.IS_OFFICIAL_RELEASE}",
        "ARTIFACTORY_URL=${env.ARTIFACTORY_URL}",
        "STAGE_REPO_NAME=${env.STAGE_REPO_NAME}",
        "DEB_COMPONENT=${env.DEB_COMPONENT}",
        "DEB_DISTRIBUTION=trusty",
        "CLONE_DIR=b"]){
        deleteDir()
        def current_workspace = pwd()
        dir("build-config"){
            checkout scm
        }
        withCredentials([
            usernamePassword(credentialsId: 'ff7ab8d2-e678-41ef-a46b-dd0e780030e1',
                             passwordVariable: 'SUDO_PASSWORD',
                             usernameVariable: 'SUDO_USER'),
            usernameColonPassword(credentialsId: 'a94afe79-82f5-495a-877c-183567c51e0b', 
                                  variable: 'BINTRAY_CREDS')]){
            timeout(90){
                withEnv(["WORKSPACE=${current_workspace}"]){
                    sh './build-config/jobs/build_docker/build_docker.sh'
                }
            }
            archiveArtifacts 'rackhd_docker_images.tar, build_record'
            stash name: 'docker', includes: 'rackhd_docker_images.tar, build_record'
            env.DOCKER_WORKSPACE="${current_workspace}"
            env.DOCKER_STASH_NAME="docker"
            env.DOCKER_STASH_PATH="rackhd_docker_images.tar"
            env.DOCKER_RECORD_STASH_PATH="build_record"
        }
        env.DOCKER_WORKSPACE="${current_workspace}"
    }
}
