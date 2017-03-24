import groovy.transform.Field;

// The default test config: ALL_TESTS (a global variable)
@Field def ALL_TESTS=[:]
ALL_TESTS["FIT"]=["TEST_GROUP":"smoke-tests","RUN_FIT_TEST":true,"RUN_CIT_TEST":false,"label":"smoke_test"]
ALL_TESTS["CIT"]=["TEST_GROUP":"smoke-tests","RUN_FIT_TEST":false,"RUN_CIT_TEST":true,"label":"smoke_test"]
ALL_TESTS["Install Ubuntu 14.04"]=["TEST_GROUP":"ubuntu-minimal-install.v2.0.test","RUN_FIT_TEST":false,"RUN_CIT_TEST":true,"label":"os_install"]
ALL_TESTS["Install ESXI 6.0"]=["TEST_GROUP":"esxi-6-min-install.v2.0.test","RUN_FIT_TEST":false,"RUN_CIT_TEST":true,"label":"os_install"]
ALL_TESTS["Install Centos 6.5"]=["TEST_GROUP":"centos-6-5-minimal-install.v2.0.test","RUN_FIT_TEST":false,"RUN_CIT_TEST":true,"label":"os_install"]

String repo_dir
String stash_manifest_name
String stash_manifest_path
String TESTS
String TEST_TYPE

def setTests(TESTS){
    this.TESTS = TESTS
}
def setRepoDir(repo_dir){
    this.repo_dir = repo_dir
}
def setType(test_type){
    this.TEST_TYPE = test_type
    env.TEST_TYPE = test_type
}
def setManifest(String manifest_name, String manifest_path){
    this.stash_manifest_name = manifest_name
    this.stash_manifest_path = manifest_path
}
def setOVA(String ova_stash_name, String ova_stash_path){
    this.ova_stash_name = ova_stash_name
    this.ova_stash_path = ova_stash_path
}
def functionTest(String test_name, String label_name, String TEST_GROUP, Boolean RUN_FIT_TEST, Boolean RUN_CIT_TEST, ArrayList<String> used_resources){
    def shareMethod = load(this.repo_dir + "/jobs/ShareMethod.groovy")
    lock(label:label_name,quantity:1){
        // Occupy an avaliable resource which contains the label
        String node_name = shareMethod.occupyAvailableLockedResource(label_name, used_resources)
        try{
            node(node_name){
                deleteDir()
                dir("build-config"){
                    checkout scm
                }

                if (this.TEST_TYPE == "manifest"){
                    // Get the manifest file
                    unstash "$stash_manifest_name"
                    env.MANIFEST_FILE="$stash_manifest_path"
            
                    // If the manifest file contains PR of on-http and RackHD, 
                    // set the environment variable MODIFY_API_PACKAGE as true
                    // The test.sh script will install api package according to API_PACKAGE_LIST
                    sh '''#!/bin/bash
                    ./build-config/build-release-tools/HWIMO-BUILD ./build-config/build-release-tools/application/parse_manifest.py \
                    --manifest-file $MANIFEST_FILE \
                    --parameters-file downstream_file
                    '''

                    env.MODIFY_API_PACKAGE = false
                    if(fileExists ('downstream_file')) {
                        def props = readProperties file: 'downstream_file'
                        if(props['REPOS_UNDER_TEST']) {
                            env.REPOS_UNDER_TEST = "${props.REPOS_UNDER_TEST}"
                            def repos = env.REPOS_UNDER_TEST.tokenize(',')
                            if(repos.contains("on-http") && repos.contains("RackHD")){
                                env.MODIFY_API_PACKAGE = true
                            }
                        }
                    }
                }

                timestamps{
                    withEnv([
                        "TEST_GROUP=$TEST_GROUP",
                        "RUN_CIT_TEST=$RUN_CIT_TEST",
                        "RUN_FIT_TEST=$RUN_FIT_TEST",
                        "SKIP_PREP_DEP=false",
                        "MANIFEST_FILE=${env.MANIFEST_FILE}",
                        "NODE_NAME=${env.NODE_NAME}",
                        "PYTHON_REPOS=ucs-service"]
                    ){
                        try{
                            timeout(60){
                                // Prepare RackHD
                                if(this.TEST_TYPE == "ova"){
                                    // env vars in this sh are defined in jobs/build_ova/ova_post_test.groovy
                                    unstash "$ova_stash_name"
                                    env.OVA_PATH = "$ova_stash_path"
                                    sh './build-config/jobs/build_ova/prepare_ova_post_test.sh'
                                }

                                if (this.TEST_TYPE == "manifest") {
                                    // This scipts can be separated into manifest_src_prepare and common_prepare
                                    sh './build-config/jobs/FunctionTest/prepare.sh'
                                }

                                // Pre-process assistant test scripts
                                sh '''#!/bin/bash -x
                                pushd build-config
                                ./build-config
                                popd
                                '''

                                // Get main test scripts for un-manifest-src test
                                if (this.TEST_TYPE != "manifest") {
                                    def exists = fileExists 'RackHD'
                                    if( !exists ){
                                        echo "Checkout RackHD for un-src test."
                                        def url = "https://github.com/RackHD/RackHD.git"
                                        def branch = "master"
                                        def targetDir = "RackHD"
                                        shareMethod.checkout(url, branch, targetDir)
                                    }
                                }
                                // Run smoke test
                                sh './build-config/test.sh'
                            }
                        } catch(error){
                            throw error
                        } finally{
                            def artifact_dir = test_name.replaceAll(' ', '-') + "[$node_name]"
                            sh '''#!/bin/bash -x
                            mkdir '''+"$artifact_dir"+'''
                            ./build-config/post-deploy.sh
                            files=$( ls build-deps/*.log )
                            if [ ! -z "$files" ];then
                                cp build-deps/*.log '''+"$artifact_dir"+'''
                            fi
                            files=$( ls RackHD/test/*.xml )
                            if [ ! -z "$files" ];then
                                cp RackHD/test/*.xml '''+"$artifact_dir" +'''
                            fi
                            '''
                            // The test_name is an argument of the method, for example: CIT
                            // It comes from the member variable: TESTS, for example: CIT.FIT
                            // The function archiveArtifactsToTarget() will unstash the stashed files
                            // according to the member variable: TESTS
                            stash name: "$test_name", includes: "$artifact_dir/*.*"
    
                            // Clean up test stack
                            sh '''#!/bin/bash -x
                            ./build-config/jobs/FunctionTest/cleanup.sh
                            '''

                            // [Based on junit xml log] Write test results to github
                            sh '''#!/bin/bash -x
                            find RackHD/test/ -maxdepth 1 -name "*.xml" > files.txt
                            files=$( paste -s -d ' ' files.txt )
                            if [ -n "$files" ];then
                                ./build-config/build-release-tools/application/parse_test_results.py \
                                --test-result-file "$files"  \
                                --parameters-file downstream_file
                            else
                                echo "No test result files generated, maybe it's aborted"
                                exit 1
                            fi
                            '''

                            // [Based on junit xml log] Determine pipeline status of this build, success or failure.
                            def junitFiles = findFiles glob: 'RackHD/test/*.xml'
                            boolean exists = junitFiles.length > 0
                            if (exists){
                                junit 'RackHD/test/*.xml'
                                int failure_count = 0
                                int error_count = 0
                                if(fileExists ("downstream_file")) {
                                    def props = readProperties file: "downstream_file"
                                    failure_count = "${props.failures}".toInteger()
                                    error_count = "${props.errors}".toInteger()
                                }
                                if (failure_count > 0 || error_count > 0){
                                    error("there are failed test cases")
                                }
                            }
                        }
                    }
                }
            }
        } finally{
            used_resources.remove(node_name)
        }
    }
}

def triggerTestsParallely(){
    def RUN_TESTS=[:]
    // TESTS is a checkbox parameter.
    // Its value is a string looks like:
    // CIT,FIT,Install Ubuntu 14.04,Install ESXI 6.0,Install Centos 6.5
    List tests = Arrays.asList(this.TESTS.split(','))
    def SIGN = ""
    if (this.TEST_TYPE == "ova"){
        SIGN = "OVA "
    }
    for(int i=0;i<tests.size();i++){
        TEST_NAME = tests[i]
        KEY = "$SIGN$TEST_NAME"
        RUN_TESTS[KEY]=ALL_TESTS[tests[i]]
    }
    def used_resources = []
    def test_branches = [:]
    
    test_names = RUN_TESTS.keySet() as String[]
    for(int i=0;i<RUN_TESTS.size();i++){
        def test_name = test_names[i]
        def label_name=RUN_TESTS[test_name]["label"]
        def test_group = RUN_TESTS[test_name]["TEST_GROUP"]
        def run_fit_test = RUN_TESTS[test_name]["RUN_FIT_TEST"]
        def run_cit_test = RUN_TESTS[test_name]["RUN_CIT_TEST"]
        test_branches[test_name] = {
            functionTest(test_name,label_name,test_group, run_fit_test, run_cit_test, used_resources)
        }
    }
    if(test_branches.size() > 0){
        parallel test_branches
    }
}

def archiveArtifactsToTarget(target){
    // The function will archive artifacts to the target
    // 1. Create a directory with name target and go to it
    // 2. Unstash files according to the member variable: TESTS, for example: CIT.FIT
    //    The function functionTest() will stash log files after run test specified in the TESTS
    // 3. Archive the directory target
    try{
        List tests = Arrays.asList(this.TESTS.split(','))
        if(tests.size() > 0){
            dir("$target"){
                for(int i=0;i<tests.size();i++){
                    def test_name = tests[i]
                    unstash "$test_name"
                }
            }
            archiveArtifacts "${target}/*.*, ${target}/**/*.*"
        }
    } catch(error){
        echo "[WARNING]Caught error during archive artifact of function test: ${error}"
    }
}

def runTest(){
    // Run test in parallel
    try{
        withEnv([
            "HTTP_STATIC_FILES=${env.HTTP_STATIC_FILES}",
            "TFTP_STATIC_FILES=${env.TFTP_STATIC_FILES}",
            "API_PACKAGE_LIST=on-http-api2.0 on-http-redfish-1.0",
            "USE_VCOMPUTE=${env.USE_VCOMPUTE}"
            ]){
            withCredentials([
                usernamePassword(credentialsId: 'ESXI_CREDS',
                                 passwordVariable: 'ESXI_PASS', 
                                 usernameVariable: 'ESXI_USER'),
                usernamePassword(credentialsId: 'SENTRY_USER', 
                                 passwordVariable: 'SENTRY_PASS', 
                                 usernameVariable: 'SENTRY_USER'), 
                usernamePassword(credentialsId: 'BMC_VNODE_CREDS', 
                                 passwordVariable: 'BMC_VNODE_PASSWORD', 
                                 usernameVariable: 'BMC_VNODE_USER'),
                string(credentialsId: 'SENTRY_HOST', variable: 'SENTRY_HOST'),
                string(credentialsId: 'SMB_USER', variable: 'SMB_USER'), 
                string(credentialsId: 'RACKHD_SMB_WINDOWS_REPO_PATH', variable: 'RACKHD_SMB_WINDOWS_REPO_PATH'),
                string(credentialsId: 'REDFISH_URL', variable: 'REDFISH_URL'), 
                string(credentialsId: 'BASE_REPO_URL', variable: 'BASE_REPO_URL'),
                string(credentialsId: 'INTERNAL_HTTP_ZIP_FILE_URL', variable: 'INTERNAL_HTTP_ZIP_FILE_URL'),
                string(credentialsId: 'INTERNAL_TFTP_ZIP_FILE_URL', variable: 'INTERNAL_TFTP_ZIP_FILE_URL')
                ]) {
                triggerTestsParallely()
            }
        }
    } catch(error){
        echo "Caught: ${error}"
        currentBuild.result = "FAILURE"
        throw error
    } 
}


def ovaPostTest(TESTS, ova_stash_name, ova_stash_path, repo_dir){
    setRepoDir(repo_dir)
    setOVA(ova_stash_name, ova_stash_path)
    setTests(TESTS)
    setType("ova")
    runTest()
}

def manifestTest(TESTS, manifest_stash_name, manifest_stash_path, repo_dir){
    setRepoDir(repo_dir)
    setManifest(manifest_stash_name, manifest_stash_path)
    setTests(TESTS)
    setType("manifest")
    runTest()
}

return this
