def generateTestBranches(function_test){
    def test_branches = [:]
    node{
        deleteDir()
        checkout scm
        def shareMethod = load("jobs/ShareMethod.groovy")
        def ALL_TESTS = function_test.getAllTests()
        def used_resources= function_test.getUsedResources()

        def DOCKER_TESTS = "${env.DOCKER_POST_TESTS}"
        def docker_test_stack = "-stack vagrant"
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
                                "DOCKER_PATH=${env.DOCKER_STASH_PATH}",
                                "DOCKER_RECORD_PATH=${env.DOCKER_RECORD_STASH_PATH}",
                                "DOCKER_RACKHD_IP=${env.DOCKER_RACKHD_IP}",
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
                                    // env vars in this sh are defined in jobs/build_ova/ova_post_test.groovy
                                    unstash "$DOCKER_STASH_NAME"
                                    sh '''#!/bin/bash
                                    ./build-config/jobs/FunctionTest/prepare_common.sh
                                    ./build-config/jobs/build_docker/prepare_docker_post_test.sh
                                    '''
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

def runTests(){
    def test_branches = generateTestBranches()
    if(test_branches.size() > 0){
        try{
            parallel test_branches
        } finally{
            archiveArtifacts()
        }
    }
}

def archiveArtifacts(){
    def DOCKER_TESTS = "${env.DOCKER_POST_TESTS}"
    node{
        deleteDir()
        checkout scm
        def function_test = load("jobs/FunctionTest/FunctionTest.groovy")
        function_test.archiveArtifactsToTarget("DOCKER_POST_SMOKE_TEST", DOCKER_TESTS)
    }
}

return this
