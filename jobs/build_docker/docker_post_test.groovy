node(build_docker_node){
    lock("docker"){
        timestamps{
            withEnv(["WORKSPACE=${env.DOCKER_WORKSPACE}"]){
                def shareMethod
                dir("Docker_Post_Test_JFiles"){
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
                                     usernameVariable: 'SUDO_USER')]
                ){
                    timeout(90){
                        sh '''#!/bin/bash +xe
                        bash $WORKSPACE/build-config/build-release-tools/post_test.sh \
                        --type docker \
                        --RackHDDir $WORKSPACE/build \
                        --buildRecord $WORKSPACE/build_record

                        echo $SUDO_PASSWORD |sudo -S chown -R $USER:$USER $WORKSPACE/rackhd               
                        '''
                    }
                }
            }
        }
    }
}

