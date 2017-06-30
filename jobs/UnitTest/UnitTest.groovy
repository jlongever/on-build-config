import groovy.transform.Field;

// It's a class for Unit Test
// load will return a instance of the class

String stash_manifest_name
String stash_manifest_path
String repo_dir
@Field label_name = "unittest"
@Field def test_repos = ["on-core", "on-tasks", "on-http", "on-taskgraph", "on-dhcp-proxy", "on-tftp", "on-syslog"]
def setManifest(String manifest_name, String manifest_path){
    this.stash_manifest_name = manifest_name
    this.stash_manifest_path = manifest_path
}

def setRepoDir(repo_dir){
    this.repo_dir = repo_dir
}

def setLableName(label_name){
    this.label_name = label_name
}

def setTestRepos(test_repos){
    this.test_repos = test_repos
}

def unitTest(repo_name, used_resources){
    // repo_name comes from the global variable test_repos
    def shareMethod = load(repo_dir + "/jobs/ShareMethod.groovy")
    lock(label:label_name,quantity:1){
        String node_name = shareMethod.occupyAvailableLockedResource(label_name, used_resources)
        try{
            node(node_name){
                deleteDir()
                dir("build-config"){
                    checkout scm
                }
                unstash "$stash_manifest_name"
                env.MANIFEST_FILE_PATH = "$stash_manifest_path"
                timeout(30){
                    try{
                        withCredentials([
                             usernamePassword(credentialsId: 'ff7ab8d2-e678-41ef-a46b-dd0e780030e1',
                                 passwordVariable: 'SUDO_PASSWORD',
                                 usernameVariable: 'SUDO_USER')
                         ]){
                             sh "./build-config/jobs/UnitTest/unit_test.sh ${repo_name}"
                         }
                    } finally{
                        // stash logs with the repo name which is the argument of the function ,for example: on-http
                        // The repo_name comes from the global variable test_repos
                        // The function archiveArtifactsToTarget() will unstash the stashed files
                        // according to the global variable: test_repos
                        stash name: "$repo_name", includes: 'xunit-reports/*.xml'
                        junit 'xunit-reports/'+"${repo_name}.xml"
    
                        sh '''
                        ./build-config/build-release-tools/application/parse_test_results.py \
                        --test-result-file xunit-reports/'''+"${repo_name}"+'''.xml  \
                        --parameters-file downstream_file
                        '''
                        // Use downstream_file to pass environment variables from shell to groovy
                        int failure_count = 0
                        if(fileExists ("downstream_file")) {
                            def props = readProperties file: "downstream_file"
                            failure_count = "${props.failures}".toInteger()
                        }
                        if (failure_count > 0){
                            error("There are failed test cases")
                        }
                    }
                }
            }
        } finally{
            used_resources.remove(node_name)
        }
    }
}

def archiveArtifactsToTarget(target){
    // The function will archive artifacts to the target
    // 1. Create a directory with name target and go to it
    // 2. Unstash files according to the global variable: test_repos, for example: ["on-http","on-core"]
    //    The function unitTest() will stash log files after run test specified in the test_repos
    // 3. Archive the directory target
    if(test_repos.size > 0){
        dir("$target"){
            for(int i=0; i<test_repos.size; i++){
                try{
                    def repo_name = test_repos.get(i)
                    unstash "$repo_name"
                } catch(error){
                    echo "[WARNING]Caught error during archive artifact of unit test: ${error}"
                }
            }
        }
        archiveArtifacts "${target}/*.*, ${target}/**/*.*"
    }
}

def runTest(String manifest_name, String manifest_path, String repo_dir){
    setManifest(manifest_name, manifest_path)
    setRepoDir(repo_dir)
    def used_resources=[]
    def test_branches = [:]
    // test_repos is a global variable
    for(int i=0; i<test_repos.size; i++){
        def repo_name = test_repos.get(i)
        test_branches["${repo_name}"] = {
            unitTest(repo_name, used_resources)
        }
    }
    if(test_branches.size() > 0){
        parallel test_branches
    }
}

return this
