import groovy.transform.Field;

// The default test config: ALL_TESTS (a global variable)
@Field def ALL_TESTS=[:]
ALL_TESTS["FIT"]=["TEST_GROUP":"-test tests -group smoke","RUN_FIT_TEST":true,"RUN_CIT_TEST":false,"label":"smoke_test", "EXTRA_HW":"ucs"]
ALL_TESTS["CIT"]=["TEST_GROUP":"smoke-tests","RUN_FIT_TEST":false,"RUN_CIT_TEST":true,"label":"smoke_test", "EXTRA_HW":""]
ALL_TESTS["Install Ubuntu 14.04"]=["TEST_GROUP":"-test tests/bootstrap/test_api20_linux_bootstrap.py -extra install_ubuntu14.04_minimum.json","RUN_FIT_TEST":true,"RUN_CIT_TEST":false,"label":"os_install", "EXTRA_HW":""]
ALL_TESTS["Install ESXI 6.0"]=["TEST_GROUP":"-test tests/bootstrap/test_api20_esxi_bootstrap.py -extra install_esxi6.0_minimum.json","RUN_FIT_TEST":true,"RUN_CIT_TEST":false,"label":"os_install", "EXTRA_HW":""]
ALL_TESTS["Install Centos 6.5"]=["TEST_GROUP":"-test tests/bootstrap/test_api20_linux_bootstrap.py -extra install_centos65_minimum.json","RUN_FIT_TEST":true,"RUN_CIT_TEST":false,"label":"os_install", "EXTRA_HW":""]

String repo_dir
String stash_manifest_name
String stash_manifest_path
String ova_stash_name
String ova_stash_path
String docker_stash_name
String docker_stash_path
String docker_record_stash_path
@Field ArrayList<String> used_resources
if (this.used_resources == null){
    this.used_resources = []
}

def setManifest(String manifest_name, String manifest_path){
    this.stash_manifest_name = manifest_name
    this.stash_manifest_path = manifest_path
}
def setOVA(String ova_stash_name, String ova_stash_path){
    this.ova_stash_name = ova_stash_name
    this.ova_stash_path = ova_stash_path
}
def setDocker(String docker_stash_name, String docker_stash_path, String docker_record_stash_path){
    this.docker_stash_name = docker_stash_name
    this.docker_stash_path = docker_stash_path
    this.docker_record_stash_path = docker_record_stash_path
}

def functionTest(String test_name, String label_name, String TEST_GROUP, Boolean RUN_FIT_TEST, Boolean RUN_CIT_TEST, String repo_dir, String test_type, String test_stack, String extra_hw){
    def shareMethod = load(repo_dir + "/jobs/ShareMethod.groovy")
    lock(label:label_name,quantity:1){
        // Occupy an avaliable resource which contains the label
        String node_name = shareMethod.occupyAvailableLockedResource(label_name, this.used_resources)
        try{
            node(node_name){
                deleteDir()
                dir("build-config"){
                    checkout scm
                }
                env.BUILD_CONFIG_DIR = "build-config"

                if (test_type == "manifest"){
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
                        "PYTHON_REPOS=ucs-service",
                        "TEST_TYPE=$test_type",
                        "TEST_STACK=$test_stack",
                        "EXTRA_HW=$extra_hw",
                        "KEEP_FAILURE_ENV=${env.KEEP_FAILURE_ENV}",
                        "KEEP_MINUTES=${env.KEEP_MINUTES}"]
                    ){
                        try{
                            timeout(90){
                                // Prepare RackHD
                                // Prepare common must before prepare all other preparations
                                sh './build-config/jobs/FunctionTest/prepare_common.sh'

                                // this step will overite current build-config and create RackHD dir
                                if (test_type == "manifest") {
                                    retry(3){
                                        // This scipts can be separated into manifest_src_prepare and common_prepare
                                        sh './build-config/jobs/FunctionTest/prepare_manifest.sh'
                                    }
                                }

                                // Get main test scripts for un-manifest-src test
                                // must before ova and docker
                                if (test_type != "manifest") {
                                    def exists = fileExists 'RackHD'
                                    if( !exists ){
                                        echo "Checkout RackHD for un-src test."
                                        def url = "https://github.com/RackHD/RackHD.git"
                                        def branch = "master"
                                        def targetDir = "RackHD"
                                        env.RackHD_DIR = targetDir
                                        shareMethod.checkout(url, branch, targetDir)
                                    }
                                }

                                // Pre-process assistant test scripts
                                sh '''#!/bin/bash -x
                                pushd build-config
                                ./build-config
                                popd
                                '''
                                // next steps must run after above steps
                                if(test_type == "ova"){
                                    // env vars in this sh are defined in jobs/build_ova/ova_post_test.groovy
                                    if (env.USE_PREBUILT_OVA == "true") {
                                        env.OVA_PATH = "$env.OVA_FILE" 
                                    } else {
                                        unstash "$ova_stash_name"
                                        env.OVA_PATH = "$ova_stash_path"
                                    }
                                    sh './build-config/jobs/build_ova/prepare_ova_post_test.sh'
                                }

                                if(test_type == "docker"){
                                    // env vars in this sh are defined in jobs/build_ova/ova_post_test.groovy
                                    unstash "$docker_stash_name"
                                    env.DOCKER_PATH = "$docker_stash_path"
                                    env.DOCKER_RECORD_PATH = "$docker_record_stash_path"
                                    sh './build-config/jobs/build_docker/prepare_docker_post_test.sh'
                                }

                                // Run smoke test
                                sh './build-config/test.sh'
                            }
                        } finally{
                            def result = "FAILURE"
                            def artifact_dir = test_name.replaceAll(' ', '-') + "[$node_name]"
                            try{
                                sh '''#!/bin/bash -x
                                set +e
                                mkdir '''+"$artifact_dir"+'''
                                ./build-config/post-deploy.sh
                                files=$( ls build-log/*.flv )
                                if [ ! -z "$files" ];then
                                    cp build-log/*.flv '''+"$artifact_dir" +'''
                                fi
                                files=$( ls RackHD/test/*.xml )
                                if [ ! -z "$files" ];then
                                    cp RackHD/test/*.xml '''+"$artifact_dir" +'''
                                fi
                                files=$( ls build-log/*.log )
                                if [ ! -z "$files" ];then
                                    cp build-log/*.log '''+"$artifact_dir"+'''
                                fi
                                if [ -d build-log/mongodb ];then
                                    cp -r build-log/mongodb '''+"$artifact_dir" +'''
                                fi
                                '''
                                def junitFiles = findFiles glob: 'RackHD/test/*.xml'
                                boolean exists = junitFiles.length > 0
                                if (exists){
                                    junit 'RackHD/test/*.xml'
                                    // [Based on junit xml log] Write test results to github
                                    sh '''#!/bin/bash -x
                                    set +e
                                    find RackHD/test/ -maxdepth 1 -name "*.xml" > files.txt
                                    files=$( paste -s -d ' ' files.txt )
                                    if [ -n "$files" ];then
                                        ./build-config/build-release-tools/application/parse_test_results.py \
                                        --test-result-file "$files"  \
                                        --parameters-file downstream_file
                                    fi
                                    '''
                                    int failure_count = 0
                                    int error_count = 0
                                    if(fileExists ("downstream_file")) {
                                        def props = readProperties file: "downstream_file"
                                        failure_count = "${props.failures}".toInteger()
                                        error_count = "${props.errors}".toInteger()
                                    }
                                    if (failure_count == 0 && error_count == 0){
                                        result = "SUCCESS"
                                    }
                                }
                                if(result == "FAILURE" && KEEP_FAILURE_ENV == "true"){
                                    int sleep_mins = Integer.valueOf(KEEP_MINUTES)
                                    def message = "Job Name: ${env.JOB_NAME} \n" + "Build Full URL: ${env.BUILD_URL} \n" + "Status: FAILURE \n" + "Stage: $test_name \n" + "Node Name: $node_name \n" + "Reserve Duration: $sleep_mins minutes \n"
                                    echo "$message"
                                    slackSend "$message"
                                    sleep time: sleep_mins, unit: 'MINUTES'
                                }
                            }finally{
                                // Clean up test stack
                                sh '''#!/bin/bash -x
                                ./build-config/jobs/FunctionTest/cleanup.sh
                                '''
                                // The test_name is an argument of the method, for example: CIT
                                // It comes from the member variable: TESTS, for example: CIT.FIT
                                // The function archiveArtifactsToTarget() will unstash the stashed files
                                // according to the member variable: TESTS
                                stash name: "$test_name", includes: "$artifact_dir/*.*, $artifact_dir/**/*.*"
                                if(result == "FAILURE"){
                                    error("there are failed test cases")
                                }
                            }
                        }
                    }
                }
            }
        } finally{
            this.used_resources.remove(node_name)
        }
    }
}

def triggerTestsParallely(TESTS, test_type, repo_dir, test_stack){
    def RUN_TESTS_DICT=[:]
    // TESTS is a checkbox parameter.
    // Its value is a string looks like:
    // CIT,FIT,Install Ubuntu 14.04,Install ESXI 6.0,Install Centos 6.5
    List tests = Arrays.asList(TESTS.split(','))
    for(int i=0;i<tests.size();i++){
        TEST_NAME = tests[i]
        KEY = "$test_type $TEST_NAME"
        RUN_TESTS_DICT[KEY]=ALL_TESTS[tests[i]]
    }

    def test_branches = [:]
    
    def RUN_TESTS = RUN_TESTS_DICT.keySet() as String[]
    for(int i=0;i<RUN_TESTS_DICT.size();i++){
        def test_name = RUN_TESTS[i]
        def label_name=RUN_TESTS_DICT[test_name]["label"]
        def test_group = RUN_TESTS_DICT[test_name]["TEST_GROUP"]
        def run_fit_test = RUN_TESTS_DICT[test_name]["RUN_FIT_TEST"]
        def run_cit_test = RUN_TESTS_DICT[test_name]["RUN_CIT_TEST"]
        def extra_hw = RUN_TESTS_DICT[test_name]["EXTRA_HW"]
        test_branches[test_name] = {
            functionTest(test_name,label_name,test_group, run_fit_test, run_cit_test, repo_dir, test_type, test_stack, extra_hw)
        }
    }
    if(test_branches.size() > 0){
        parallel test_branches
    }
}

def archiveArtifactsToTarget(target, TESTS, test_type){
    // The function will archive artifacts to the target
    // 1. Create a directory with name target and go to it
    // 2. Unstash files according to the member variable: TESTS, for example: CIT.FIT
    //    The function functionTest() will stash log files after run test specified in the TESTS
    // 3. Archive the directory target
    List tests = Arrays.asList(TESTS.split(','))
    if(tests.size() > 0){
        dir("$target"){
            for(int i=0;i<tests.size();i++){
                try{
                    test = tests[i]
                    def test_name = "$test_type $test"
                    unstash "$test_name"
                } catch(error){
                    echo "[WARNING]Caught error during archive artifact of function test: ${error}"
                }
            }
        }
        archiveArtifacts "${target}/*.*, ${target}/**/*.*"
    }
}

def runTest(TESTS, test_type, repo_dir, test_stack){
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
                usernamePassword(credentialsId: 'ff7ab8d2-e678-41ef-a46b-dd0e780030e1',
                                 passwordVariable: 'SUDO_PASSWORD',
                                 usernameVariable: 'SUDO_USER'),
                string(credentialsId: 'SENTRY_HOST', variable: 'SENTRY_HOST'),
                string(credentialsId: 'SMB_USER', variable: 'SMB_USER'), 
                string(credentialsId: 'RACKHD_SMB_WINDOWS_REPO_PATH', variable: 'RACKHD_SMB_WINDOWS_REPO_PATH'),
                string(credentialsId: 'REDFISH_URL', variable: 'REDFISH_URL'), 
                string(credentialsId: 'BASE_REPO_URL', variable: 'BASE_REPO_URL'),
                string(credentialsId: 'INTERNAL_HTTP_ZIP_FILE_URL', variable: 'INTERNAL_HTTP_ZIP_FILE_URL'),
                string(credentialsId: 'INTERNAL_TFTP_ZIP_FILE_URL', variable: 'INTERNAL_TFTP_ZIP_FILE_URL')
                ]) {
                triggerTestsParallely(TESTS, test_type, repo_dir, test_stack)
            }
        }
    } catch(error){
        echo "Caught: ${error}"
        currentBuild.result = "FAILURE"
        throw error
    } 
}

def dockerPostTest(TESTS, docker_stash_name, docker_stash_path, docker_record_stash_path, repo_dir, test_type){
    setDocker(docker_stash_name, docker_stash_path, docker_record_stash_path)
    test_stack = "-stack vagrant"
    runTest(TESTS, test_type, repo_dir, test_stack)
}

def ovaPostTest(TESTS, ova_stash_name, ova_stash_path, repo_dir, test_type){
    setOVA(ova_stash_name, ova_stash_path)
    test_stack = "-stack ova"
    runTest(TESTS, test_type, repo_dir, test_stack)
}

def manifestTest(TESTS, manifest_stash_name, manifest_stash_path, repo_dir, test_type){
    setManifest(manifest_stash_name, manifest_stash_path)
    test_stack = "-stack vagrant"
    runTest(TESTS, test_type, repo_dir, test_stack)
}

return this
