// It's a class of pr gate unit test
// It uses an instance of UnitTest to reuse function of UnitTest
String stash_manifest_name
String stash_manifest_path
String repo_dir
def unit_test

def setRepoDir(repo_dir){
    this.repo_dir = repo_dir
}

def setUnitTest(){
    this.unit_test = load(repo_dir + "/jobs/UnitTest/UnitTest.groovy")
}

def setManifest(String manifest_name, String manifest_path){
    this.stash_manifest_name = manifest_name
    this.stash_manifest_path = manifest_path
    unit_test.setManifest(manifest_name, manifest_path)
}

def setTestRepos(){
    dir(repo_dir){
        unstash "$stash_manifest_name"
    }
    env.MANIFEST_FILE_PATH = repo_dir + "/${this.stash_manifest_path}"

    // Parse manifest to get the repositories which should run unit test
    // For a PR of on-core, 
    // the test_repos=["on-core", "on-tasks", "on-http", "on-taskgraph", "on-dhcp-proxy", "on-tftp", "on-syslog"]
    // For an independent PR of on-http
    // the test_repos=["on-http"]
    sh '''#!/bin/bash
    pushd ''' + "$repo_dir" + '''
    ./build-release-tools/HWIMO-BUILD ./build-release-tools/application/parse_manifest.py \
    --manifest-file $MANIFEST_FILE_PATH \
    --parameters-file downstream_file
    '''
    def repos_need_unit_test = ""
    if(fileExists ('downstream_file')) {
        def props = readProperties file: 'downstream_file'
        if(props['REPOS_NEED_UNIT_TEST']) {
            repos_need_unit_test = "${props.REPOS_NEED_UNIT_TEST}"
        }
    }
    def test_repos = repos_need_unit_test.tokenize(',')
    unit_test.setTestRepos(test_repos)
   
}

def runTest(String manifest_name, String manifest_path, String repo_dir){
    setRepoDir(repo_dir)
    setUnitTest()
    setManifest(manifest_name, manifest_path)
    setTestRepos()
    unit_test.runTest(manifest_name, manifest_path, repo_dir)
}

return this
