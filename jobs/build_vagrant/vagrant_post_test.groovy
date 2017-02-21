node(build_vagrant_node){
    lock("packer_bri"){
         timestamps{           
            withEnv([
                "WORKSPACE=${env.VAGRANT_WORKSPACE}"]){
                def shareMethod
                dir("Vagrant_Post_Test_JFiles"){
                    checkout scm
                    shareMethod = load("jobs/shareMethod.groovy")
                }
                def url = "https://github.com/RackHD/on-build-config.git"
                def branch = "*/master"
                def targetDir = "build-config"
                shareMethod.checkout(url, branch, targetDir)
                timeout(90){
                    sh './Vagrant_Post_Test_JFiles/jobs/build_vagrant/vagrant_post_test.sh'
                }
            }
        }
    }
}
