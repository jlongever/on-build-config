import groovy.transform.Field;

// The default test config: ALL_TESTS (a global variable)
@Field def ALL_TESTS = [:]
ALL_TESTS["FIT"]=["TEST_GROUP":"-test tests -group smoke","label":"smoke_test", "EXTRA_HW":""]
ALL_TESTS["OS_INSTALL"]=["TEST_GROUP":"-test tests/bootstrap/pr_gate_os_install.py","label":"os_install", "EXTRA_HW":""]
ALL_TESTS["Install Ubuntu 14.04"]=["TEST_GROUP":"-test tests/bootstrap/pr_gate_os_install.py","label":"os_install", "EXTRA_HW":""]
// ALL_TESTS["Install Ubuntu 14.04"]=["TEST_GROUP":"-test tests/bootstrap/test_api20_linux_bootstrap.py -extra install_ubuntu14.04_minimum.json","label":"os_install", "EXTRA_HW":""]
ALL_TESTS["Install ESXI 6.0"]=["TEST_GROUP":"-test tests/bootstrap/test_api20_esxi_bootstrap.py -extra install_esxi6.0_minimum.json","label":"os_install", "EXTRA_HW":""]
ALL_TESTS["Install Centos 6.5"]=["TEST_GROUP":"-test tests/bootstrap/test_api20_linux_bootstrap.py -extra install_centos65_minimum.json","label":"os_install", "EXTRA_HW":""]

@Field ArrayList<String> used_resources = []

def getAllTests(){
    return ALL_TESTS
}

def getUsedResources(){
    return used_resources
}

def functionTest(String test_name, String test_type, String TEST_GROUP, String test_stack, String extra_hw){
    withEnv([
        "API_PACKAGE_LIST=on-http-api2.0 on-http-redfish-1.0",
        "USE_VCOMPUTE=${env.USE_VCOMPUTE}",
        "TEST_GROUP=$TEST_GROUP",
        "NODE_NAME=${env.NODE_NAME}",
        "TEST_STACK=$test_stack",
        "EXTRA_HW=$extra_hw",
        "KEEP_FAILURE_ENV=${env.KEEP_FAILURE_ENV}",
        "KEEP_MINUTES=${env.KEEP_MINUTES}"])
    {
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
            string(credentialsId: 'BASE_REPO_URL', variable: 'BASE_REPO_URL')
        ]) {
            try{
                timeout(90){
                    // run test script
                    sh '''#!/bin/bash -x
                    pushd build-config
                    ./build-config
                    popd
                    ./build-config/test.sh
                    '''
                }
            } finally{
                test_name = "$test_type $test_name"
                def result = "FAILURE"
                def artifact_dir = test_name.replaceAll(' ', '-') + "[$NODE_NAME]"
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
 
                    find RackHD/test/ -maxdepth 1 -name "*.xml" > files.txt
                    files=$( paste -s -d ' ' files.txt )
                    if [ -n "$files" ];then
                        ./build-config/build-release-tools/application/parse_test_results.py \
                        --test-result-file "$files"  \
                        --parameters-file downstream_file
                    else
                        echo "No any test report generated"
                        echo "tests=0" > downstream_file
                    fi
                    '''
                    int failure_count = 0
                    int error_count = 0
                    int tests_count = 0
                    if(fileExists ("downstream_file")) {
                        def props = readProperties file: "downstream_file"
                        tests_count = "${props.tests}".toInteger()
                        if (tests_count > 0){
                            junit 'RackHD/test/*.xml'
                            failure_count = "${props.failures}".toInteger()
                            error_count = "${props.errors}".toInteger()
                            if (failure_count == 0 && error_count == 0){
                                result = "SUCCESS"
                            }
                        }
                    }
                    if(result == "FAILURE"){
                        if(test_type == "manifest" && KEEP_DOCKER_ON_FAILURE == "true") {
                            def docker_tag = JOB_NAME + "_" + test_name.replaceAll(' ', '-') + ":" + BUILD_NUMBER
                            sh '''#!/bin/bash -x
                            set +e
                            pushd $WORKSPACE
                            ./build-config/jobs/pr_gate/save_docker.sh ''' + "$docker_tag" + '''
                            cp build-log/*.log '''+"$artifact_dir"+'''
                            popd
                            '''
                        }
                        if(KEEP_FAILURE_ENV == "true"){
                            int sleep_mins = Integer.valueOf(KEEP_MINUTES)
                            def message = "Job Name: ${env.JOB_NAME} \n" + "Build Full URL: ${env.BUILD_URL} \n" + "Status: FAILURE \n" + "Stage: $test_name \n" + "Node Name: $node_name \n" + "Reserve Duration: $sleep_mins minutes \n"
                            echo "$message"
                            slackSend "$message"
                            sleep time: sleep_mins, unit: 'MINUTES'
                        }
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

def archiveArtifactsToTarget(target, TESTS, test_type){
    // The function will archive artifacts to the target
    // 1. Create a directory with name target and go to it
    // 2. Unstash files according to the member variable: TESTS, for example: CIT.FIT
    //    The function functionTest() will stash log files after run test specified in the TESTS
    // 3. Archive the directory target
     if(TESTS == "null" || TESTS == "" || TESTS == null){
        print "No function test run, skip archiveArtifacts"
        return
    }
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

return this
