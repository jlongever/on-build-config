import groovy.transform.Field;
@Field def shareMethod
node{
    deleteDir()
    checkout scm
    shareMethod = load("jobs/ShareMethod.groovy")
}

lock("ova_build"){
    String label_name = "packer_ova"
    lock(label:label_name,quantity:1){
        resources_name = shareMethod.getLockedResourceName(label_name)
        if(resources_name.size>0){
            node_name = resources_name[0]
        }
        else{
            error("Failed to find resource with label " + label_name)
        }
        node(node_name){ws{
            timestamps{
                withEnv([
                    "RACKHD_COMMIT=${env.RACKHD_COMMIT}",
                    "RACKHD_VERSION=${env.RACKHD_VERSION}",
                    "IS_OFFICIAL_RELEASE=${env.IS_OFFICIAL_RELEASE}",
                    "OVA_CACHE_BUILD=${env.OVA_CACHE_BUILD}",
                    "OS_VER=${env.OS_VER}",
                    "BUILD_TYPE=vmware", 
                    "BINTRAY_SUBJECT=${env.BINTRAY_SUBJECT}",
                    "BINTRAY_REPO=debian",
                    "CI_BINTRAY_SUBJECT=${env.CI_BINTRAY_SUBJECT}",
                    "CI_BINTRAY_REPO=debian", 
                    "BINTRAY_COMPONENT=main", 
                    "BINTRAY_DISTRIBUTION=trusty", 
                    "BINTRAY_ARCHITECTURE=amd64"]){
                    def current_workspace = pwd()
                    deleteDir()
                    dir("on-build-config"){
                        checkout scm
                    }
                    def url = "https://github.com/RackHD/RackHD.git"
                    def branch = "${env.RACKHD_COMMIT}"
                    def targetDir = "build"
                    shareMethod.checkout(url, branch, targetDir)
                    // Test jenkins server doesn't use OVA cache build 
                    if (OVA_CACHE_BUILD == "true"){
                        step ([$class: 'CopyArtifact',
                        projectName: 'OVA_CACHE_BUILD',
                        target: 'cache_image']);
                    }
                    timeout(180){
                        withEnv(["WORKSPACE=${current_workspace}"]){
                            sh './on-build-config/jobs/build_ova/build_ova.sh'
                        }
                    }
                    archiveArtifacts 'build/packer/*.ova, build/packer/*.log, build/packer/*.md5, build/packer/*.sha'
                    stash name: 'ova', includes: 'build/packer/*.ova'
                    env.OVA_WORKSPACE="${current_workspace}"
                    env.OVA_STASH_NAME="ova"
                    env.OVA_PATH="build/packer/*.ova"
                }
            }
        }
    }
}}

