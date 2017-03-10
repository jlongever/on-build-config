def checkout(String url, String branch, String targetDir){
    checkout(
    [$class: 'GitSCM', branches: [[name: branch]],
    extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: targetDir]],
    userRemoteConfigs: [[url: url]]])
}
def checkout(String url, String branch){
    checkout(
    [$class: 'GitSCM', branches: [[name: branch]],
    userRemoteConfigs: [[url: url]]])
}

def checkout(String url){
    checkout(url, "master")
}

def buildAndPublish(){
    stage("Packages Build"){
        load("jobs/build_debian/build_debian.groovy")
    }

    stage("Images Build"){
        parallel 'vagrant build':{
            load("jobs/build_vagrant/build_vagrant.groovy")
        }, 'ova build':{
            load("jobs/build_ova/build_ova.groovy")
        }, 'build docker':{
            load("jobs/build_docker/build_docker.groovy")
           load("jobs/build_docker/build_docker.groovy")
        }
    }

    stage("Post Test"){
        parallel 'vagrant post test':{
            load("jobs/build_vagrant/vagrant_post_test.groovy")
        }, 'ova post test':{
            load("jobs/build_ova/ova_post_test.groovy")
        }, 'docker post test':{
            load("jobs/build_docker/docker_post_test.groovy")
        }
    }
  
    stage("Publish"){
        parallel 'Publish Debian':{
            load("jobs/release/release_debian.groovy")
        }, 'Publish Vagrant':{
            load("jobs/release/release_vagrant.groovy")
        }, 'Publish Docker':{
            load("jobs/release/release_docker.groovy")
        }, 'Publish NPM':{
            load("jobs/release/release_npm.groovy")
        }
    }
}
return this
