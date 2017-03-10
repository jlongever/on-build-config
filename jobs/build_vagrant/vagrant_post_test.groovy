node(build_vagrant_node){
    lock("packer_bri"){
         timestamps{           
            withEnv([
                "WORKSPACE=${env.VAGRANT_WORKSPACE}"]){
                dir("build-config"){
                    checkout scm
                }
                timeout(90){
                    sh './build-config/jobs/build_vagrant/vagrant_post_test.sh'
                }
            }
        }
    }
}
