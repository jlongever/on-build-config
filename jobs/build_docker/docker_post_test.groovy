node(build_docker_node){
    lock("docker"){
        timestamps{
        
            def shareMethod
            dir("Docker_Post_Test_JFiles"){
                checkout scm
                shareMethod = load("jobs/shareMethod.groovy")
            }

            def url = "https://github.com/RackHD/on-build-config.git"
            def branch = "master"
            def targetDir = "build-config"
            shareMethod.checkout(url, branch, targetDir)
  
            unstash "docker_build_record"

            timeout(90){
                sh '''#!/bin/bash +xe

                #for test
                git clone https://github.com/changev/rackhd
                cd rackhd
                git checkout feature/docker-compose-pull-file-image
                cd ..
                #

                cd build/docker

                bash $WORKSPACE/build-config/build-release-tools/post_test.sh \
                --type docker \
                --RackHDDir $WORKSPACE/rackhd \
                --buildRecord $WORKSPACE/build_record
                '''
            }
        }
    }
}

