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

def getLockedResourceName(String label_name){
    // Get the resource name whose label contains the parameter label_name
    // The locked resources of the build
    def resources=org.jenkins.plugins.lockableresources.LockableResourcesManager.class.get().getResourcesFromBuild(currentBuild.getRawBuild())
    def resources_name=[]
    for(int i=0;i<resources.size();i++){
        String labels = resources[i].getLabels();
        List label_names = Arrays.asList(labels.split("\\s+"));
        for(int j=0;j<label_names.size();j++){
            if(label_names[j]==label_name){
                resources_name.add(resources[i].getName());
            }
        }
    }
    return resources_name
}

def occupyAvailableLockedResource(String label_name, ArrayList<String> used_resources){
     // The locked resources whose label contains the parameter label_name
    resources = getLockedResourceName(label_name)
    def available_resources = resources - used_resources
    if(available_resources.size > 0){
        used_resources.add(available_resources[0])
        String resource_name = available_resources[0]
        return resource_name
    }
    else{
        error("There is no available resources for $label_name")
    }
}

def buildPackage(String repo_dir){
    // retry times for package build to avoid failing caused by network
    int retry_times = 3
    stage("Packages Build"){
        retry(retry_times){
            load(repo_dir + "/jobs/build_debian/build_debian.groovy")
        }
    }
}

def testOVA(String repo_dir){
    def function_test = load(repo_dir + "/jobs/FunctionTest/FunctionTest.groovy")
    def ova_post_test = load(repo_dir + "/jobs/build_ova/ova_post_test.groovy")
    ova_post_test.runTests(function_test)
}

def testDocker(String repo_dir){
    def function_test = load(repo_dir + "/jobs/FunctionTest/FunctionTest.groovy")
    def docker_post_test = load(repo_dir + "/jobs/build_docker/docker_post_test.groovy")
    docker_post_test.runTests(function_test)
}

def testVagrant(String repo_dir){
    load(repo_dir + "/jobs/build_vagrant/vagrant_post_test.groovy")
}

def buildOVA(String repo_dir){
    load(repo_dir + "/jobs/build_ova/build_ova.groovy")
}

def buildDocker(String repo_dir){
    load(repo_dir + "/jobs/build_docker/build_docker.groovy")
}

def buildVagrant(String repo_dir){
    load(repo_dir + "/jobs/build_vagrant/build_vagrant.groovy")
}

def buildImages(String repo_dir){
    // retry times for images build to avoid failing caused by network
    int retry_times = 3
    stage("Images Build"){
        parallel 'vagrant build':{
            retry(retry_times){
                buildVagrant(repo_dir)
            }
        }, 'ova build':{
            retry(retry_times){
                buildOVA(repo_dir)
            }
        }, 'build docker':{
            retry(retry_times){
                buildDocker(repo_dir)
            }
        }
    }

    stage("Post Test"){
        load(repo_dir + "/jobs/FunctionTest/PostTest.groovy")
    }
}

def buildandtestOVA(String repo_dir){
    // retry times for images build to avoid failing caused by network
    int retry_times = 3

    buildPackage(repo_dir)

    stage("OVA Images Build"){
        retry(retry_times){
            buildOVA(repo_dir)
        }
    }

    stage("OVA Post Test"){
        testOVA(repo_dir)
    }
}

def buildandtestDocker(String repo_dir){
    // retry times for images build to avoid failing caused by network
    int retry_times = 3

    buildPackage(repo_dir)

    stage("Docker Images Build"){
        retry(retry_times){
            buildDocker(repo_dir)
        }
    }

    stage("Docker Post Test"){
        testDocker(repo_dir)
    }
}

def publishImages(String repo_dir){
    stage("Publish"){
        parallel 'Publish Debian':{
            load(repo_dir + "/jobs/release/release_debian.groovy")
        }, 'Publish Vagrant':{
            load(repo_dir + "/jobs/release/release_vagrant.groovy")
        }, 'Publish Docker':{
            load(repo_dir + "/jobs/release/release_docker.groovy")
        }, 'Publish NPM':{
            load(repo_dir + "/jobs/release/release_npm.groovy")
        }
    }
}

def createTag(String repo_dir){
    stage("Create Tag"){
        load(repo_dir + "/jobs/SprintRelease/create_tag.groovy")
    }
}

def buildAndPublish(Boolean publish, Boolean tag, String repo_dir){
    buildPackage(repo_dir)

    buildImages(repo_dir)

    if(tag){
        createTag(repo_dir)
    }
    if(publish){
        publishImages(repo_dir)
    }
}

def sendResult(boolean sendJenkinsBuildResults, boolean sendTestResults){
    stage("Send Test Result"){
        try{
            if ("${currentBuild.result}" != "SUCCESS"){
                currentBuild.result = "FAILURE"
            }
            step([$class: 'VTestResultsAnalyzerStep', sendJenkinsBuildResults: sendJenkinsBuildResults, sendTestResults: sendTestResults])
            def message = "Job Name: ${env.JOB_NAME} \n" + "Build Full URL: ${env.BUILD_URL} \n" + "Status: " + currentBuild.result + "\n"
            echo "$message"
            slackSend "$message"
        } catch(error){
            echo "Caught: ${error}"
        }
    }
}

def downloadManifest(String url, String target){
    withCredentials([
            usernamePassword(credentialsId: 'a94afe79-82f5-495a-877c-183567c51e0b',
            passwordVariable: 'BINTRAY_API_KEY',
            usernameVariable: 'BINTRAY_USERNAME')
    ]){
        sh 'curl --user $BINTRAY_USERNAME:$BINTRAY_API_KEY --retry 5 --retry-delay 5 ' + "$url" + ' -o ' + "${target}"
    }
}

def generateManifestFromPR(String manifest_path){
    // Create a manifest file as manifest_path which specifies the info of repo/branch under PR test, 
    // according to variable ghprbGhRepository and sha1 ( build-in variable defined by Jenkins plugin GHPRB )
    def manifest = new net.sf.json.JSONObject()
    String repository_url = "https://github.com/${ghprbGhRepository}.git"
    manifest.putAll([
        "repositories":[
                [
                "branch":"",
                "commit-id":sha1,             // such as origin/pr/9/merge
                "repository":repository_url,  // such as https://github.com/RackHD/image-service.git
                "under-test": true
                ]
            ]
        ])
    writeJSON file: manifest_path, json: manifest   
}

def writeBackToGitHub(String library_dir, String manifest_path){
    try{
        // if previous steps all pass,  $currentBuild.result will be set to "SUCCESS" explictly in pipeline groovy code
        // if Junit plugin found test case error in previous step,  the plugin will set $currentBuild.result  to "Unstable"
        // if previous steps abort with error, the $currentBuild.result will not get chance to be set . so value is "null" here
        // ------
        //Jenkins currentBuild.result| github commit status(https://developer.github.com/v3/repos/statuses/ )
        // null                      | failure
        // failure                   | failure
        // unstable                  | failure
        // success                   | success
        if ("${currentBuild.result}" != "SUCCESS"){
            currentBuild.result = "FAILURE"
        }
        withCredentials([string(credentialsId: 'JENKINSRHD_GITHUB_TOKEN',
                        variable: 'GITHUB_TOKEN')]){
            sh """#!/bin/bash -ex
            pushd ${library_dir}
            ./jobs/write_back_github/write_back_github.sh ${library_dir} ${manifest_path} ${currentBuild.result}
            popd
            """
        }
        
    } catch(error){
        echo "Caught: ${error}"
    }
}
return this
