def generateTestBranches(function_test){
    def test_branches = [:]
    node{
        deleteDir()
        checkout scm
        def shareMethod = load("jobs/ShareMethod.groovy")
        def ALL_TESTS = function_test.getAllTests()
        def used_resources= function_test.getUsedResources()

        def DOCKER_TESTS = "${env.DOCKER_POST_TESTS}"
        def docker_test_stack = "-stack docker"
        List docker_tests_group = Arrays.asList(DOCKER_TESTS.split(','))
        for(int i=0; i<docker_tests_group.size(); i++){
            def test_name = docker_tests_group[i]
            def label_name=ALL_TESTS[test_name]["label"]
            def test_group = ALL_TESTS[test_name]["TEST_GROUP"]
            def run_fit_test = ALL_TESTS[test_name]["RUN_FIT_TEST"]
            def run_cit_test = ALL_TESTS[test_name]["RUN_CIT_TEST"]
            def extra_hw = ALL_TESTS[test_name]["EXTRA_HW"]
            test_branches["docker $test_name"] = {
                String node_name = ""
                try{
                    lock(label:label_name,quantity:1){
                        // Occupy an avaliable resource which contains the label
                        node_name = shareMethod.occupyAvailableLockedResource(label_name, used_resources)
                        node(node_name){
                            withEnv([
                                "DOCKER_STASH_NAME=${env.DOCKER_STASH_NAME}",
                                "DOCKER_RACKHD_IP=${env.DOCKER_RACKHD_IP}",
                                "stash_manifest_name=${env.stash_manifest_name}",
                                "stash_manifest_path=${env.stash_manifest_path}",
                                "SKIP_PREP_DEP=false",
                                "USE_VCOMPUTE=${env.USE_VCOMPUTE}",
                                "TEST_TYPE=docker"])
                            {
                                withCredentials([
                                    usernamePassword(credentialsId: 'ESXI_CREDS',
                                                    passwordVariable: 'ESXI_PASS',
                                                    usernameVariable: 'ESXI_USER'),
                                    usernamePassword(credentialsId: 'ff7ab8d2-e678-41ef-a46b-dd0e780030e1',
                                                    passwordVariable: 'SUDO_PASSWORD',
                                                    usernameVariable: 'SUDO_USER')])
                                {
                                    try{
                                        deleteDir()
                                        dir("build-config"){
                                            checkout scm
                                        }
                                        env.BUILD_CONFIG_DIR = "build-config"
                                        echo "Checkout RackHD for un-src test."
                                        def url = "https://github.com/RackHD/RackHD.git"
                                        def branch = "master"
                                        def targetDir = "RackHD"
                                        env.RackHD_DIR = targetDir
                                        shareMethod.checkout(url, branch, targetDir)
                                        
                                        if (env.USE_PREBUILT_IMAGES == "true"){
                                            if (env.DOCKER_IMAGES.contains("http")){
                                                sh 'wget -c -nv -O rackhd_docker_images.tar $DOCKER_IMAGES'
                                                env.DOCKER_PATH = pwd() + "/rackhd_docker_images.tar"
                                            } else {
                                                env.DOCKER_PATH = "$env.DOCKER_IMAGES"
                                            } 
                                        } else {
                                            unstash "$DOCKER_STASH_NAME"
                                            env.DOCKER_PATH="${env.DOCKER_STASH_PATH}"
                                            env.DOCKER_RECORD_PATH="${env.DOCKER_RECORD_STASH_PATH}"
                                        }
                                        sh '''#!/bin/bash
                                        ./build-config/jobs/FunctionTest/prepare_common.sh
                                        ./build-config/jobs/build_docker/prepare_docker_post_test.sh
                                        '''

                                        // Add commit/version checking in docker-post-test
                                        println "[DEBUG] stash_manifest_name:" + "$stash_manifest_name"
                                        unstash "$stash_manifest_name"
                                        env.MANIFEST_FILE="$stash_manifest_path"

                                        env.DOCKER_REPO_HASHCODE_FILE = env.RackHD_DIR + "/docker/docker_repo_hashcode.txt"
                                        sh "/bin/bash ./build-config/jobs/build_docker/get_docker_commit_version.sh ${DOCKER_RECORD_PATH} ${DOCKER_REPO_HASHCODE_FILE}"
                                        sh '''#!/bin/bash
                                        ./build-config/build-release-tools/HWIMO-BUILD ./build-config/build-release-tools/application/docker_version_check.py \
                                        --manifest-file $MANIFEST_FILE \
                                        --parameters-file $DOCKER_REPO_HASHCODE_FILE
                                        '''
                                    } catch(error){
                                        // Clean up test stack
                                        sh '''#!/bin/bash -x
                                        ./build-config/jobs/FunctionTest/cleanup.sh
                                        '''
                                        echo "Caught: ${error}"
                                        error("Preparation of docker post test failed.")
                                    }
                                    // Start to run test
                                    function_test.functionTest(test_name, test_group, run_fit_test, run_cit_test, docker_test_stack, extra_hw)
                                }
                            }
                        }
                    }
                } finally{
                    used_resources.remove(node_name)
                }
            }
        }
    }
    return test_branches
}

def runTests(function_test){
    def test_branches = generateTestBranches(function_test)
    if(test_branches.size() > 0){
        try{
            parallel test_branches
        } finally{
            archiveArtifacts(function_test)
        }
    }
}

def archiveArtifacts(function_test){
    def DOCKER_TESTS = "${env.DOCKER_POST_TESTS}"
    function_test.archiveArtifactsToTarget("DOCKER_POST_SMOKE_TEST", DOCKER_TESTS)
}

return this
