import groovy.transform.Field;
@Field def shareMethod
node{
    deleteDir()
    checkout scm
    shareMethod = load("jobs/ShareMethod.groovy")
}

String label_name = "packer_vagrant"
lock(label:label_name,quantity:1){
    resources_name = shareMethod.getLockedResourceName(label_name)
    if(resources_name.size>0){
        node_name = resources_name[0]
    }
    else{
        error("Failed to find resource with label " + label_name)
    }
    node(node_name){
        deleteDir()
        unstash "vagrant"
        dir("build-config"){
            checkout scm
        }
        timeout(90){
            sh './build-config/jobs/build_vagrant/vagrant_post_test.sh'
        }
    }
}
