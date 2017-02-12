node(build_docker_node){
    lock("docker"){
        timestamps{
            dir("Release_Docker_JFiles"){
                checkout scm
            }
                
            withCredentials([
                usernamePassword(credentialsId: 'da1e60c6-f23a-429d-b0f5-19e3b287f5dc', 
                                 passwordVariable: 'DOCKERHUB_PASS', 
                                 usernameVariable: 'DOCKERHUB_USER')]) {

                timeout(120){
                    sh './Release_Docker_JFiles/jobs/release/release_docker.sh'

                }
            }
        }
    }
}

