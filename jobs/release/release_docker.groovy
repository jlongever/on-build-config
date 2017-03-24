node(build_docker_node){
    timestamps{
        dir("on-build-config"){
            checkout scm
        }
        dir("DOCKER"){
            unstash env.DOCKER_STASH_NAME
        }
        withCredentials([
            usernamePassword(credentialsId: 'da1e60c6-f23a-429d-b0f5-19e3b287f5dc', 
                             passwordVariable: 'DOCKERHUB_PASS', 
                             usernameVariable: 'DOCKERHUB_USER')]) {
            timeout(120){
                sh './on-build-config/jobs/release/release_docker.sh'
            }
        }
    }
}

