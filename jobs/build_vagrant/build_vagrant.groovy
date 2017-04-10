node(build_vagrant_node){
    lock("packer_usa"){
        timestamps{
            withEnv([
                "RACKHD_COMMIT=${env.RACKHD_COMMIT}",
                "RACKHD_VERSION=${env.RACKHD_VERSION}",
                "IS_OFFICIAL_RELEASE=${env.IS_OFFICIAL_RELEASE}",
                "OS_VER=${env.OS_VER}",
                "BUILD_TYPE=virtualbox", 
                "BINTRAY_SUBJECT=rackhd-mirror", 
                "CI_BINTRAY_REPO=debian", 
                "BINTRAY_COMPONENT=main", 
                "BINTRAY_DISTRIBUTION=trusty", 
                "BINTRAY_ARCHITECTURE=amd64"]){
                def current_workspace = pwd()
                deleteDir()
                def shareMethod
                dir("Build_Vagrant_JFiles"){
                    checkout scm
                    shareMethod = load("jobs/ShareMethod.groovy")
                }
                def url = "https://github.com/RackHD/RackHD.git"
                def branch = "${env.RACKHD_COMMIT}"
                def targetDir = "build"
                shareMethod.checkout(url, branch, targetDir)
                
                timeout(180){
                    withEnv(["WORKSPACE=${current_workspace}"]){
                        sh './Build_Vagrant_JFiles/jobs/build_vagrant/build_vagrant.sh'
                    }
                }
                archiveArtifacts 'build/packer/*.box, build/packer/*.log'
                stash name: 'vagrant', includes: 'build/packer/*.box'
                env.VAGRANT_WORKSPACE="${current_workspace}"
                echo "${env.VAGRANT_WORKSPACE}"
            }
        }
    }
}
