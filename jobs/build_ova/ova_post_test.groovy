import groovy.transform.Field;

@Field def TEST_TYPE = "ova"

def generateTestBranches(function_test){
    def test_branches = [:]
    node{
        deleteDir()
        checkout scm
        def shareMethod = load("jobs/ShareMethod.groovy")
        def ALL_TESTS = function_test.getAllTests()
        def used_resources= function_test.getUsedResources()

        // ova post test
        def OVA_TESTS = "${env.OVA_POST_TESTS}"
        def ova_test_stack = "-stack ova"
        List ova_tests_group = Arrays.asList(OVA_TESTS.split(','))
        for(int i=0; i<ova_tests_group.size(); i++){
            def test_name = ova_tests_group[i]
            def label_name=ALL_TESTS[test_name]["label"]
            def test_group = ALL_TESTS[test_name]["TEST_GROUP"]
            def run_fit_test = ALL_TESTS[test_name]["RUN_FIT_TEST"]
            def run_cit_test = ALL_TESTS[test_name]["RUN_CIT_TEST"]
            def extra_hw = ALL_TESTS[test_name]["EXTRA_HW"]
            test_branches["ova $test_name"] = {
                String node_name = ""
                try{
                    lock(label:label_name,quantity:1){
                        // Occupy an avaliable resource which contains the label
                        node_name = shareMethod.occupyAvailableLockedResource(label_name, used_resources)
                        node(node_name){
                            withEnv([
                                "IS_OFFICIAL_RELEASE=${env.IS_OFFICIAL_RELEASE}",
                                "RACKHD_VERSION=${env.RACKHD_VERSION}",
                                "OVA_STASH_NAME=${env.OVA_STASH_NAME}",
                                "OS_VER=${env.OS_VER}",
                                "OVA_GATEWAY=${env.OVA_GATEWAY}",
                                "SKIP_PREP_DEP=false",
                                "USE_VCOMPUTE=${env.USE_VCOMPUTE}",
                                "OVA_NET_INTERFACE=${env.OVA_NET_INTERFACE}",
                                "DNS_SERVER_IP=${env.DNS_SERVER_IP}",
                                "BUILD_ID=${env.BUILD_ID}", //Jenkins Build-in Env
                                "TEST_TYPE=${TEST_TYPE}"])
                            {
                                withCredentials([
                                    usernamePassword(credentialsId: 'OVA_CREDS',
                                                    passwordVariable: 'OVA_PASSWORD',
                                                    usernameVariable: 'OVA_USER'),
                                    usernamePassword(credentialsId: 'ESXI_CREDS',
                                                    passwordVariable: 'ESXI_PASS',
                                                    usernameVariable: 'ESXI_USER'),
                                    usernamePassword(credentialsId: 'ff7ab8d2-e678-41ef-a46b-dd0e780030e1',
                                                    passwordVariable: 'SUDO_PASSWORD',
                                                    usernameVariable: 'SUDO_USER'),
                                     usernamePassword(credentialsId: 'BMC_VNODE_CREDS',
                                                    passwordVariable: 'BMC_VNODE_PASSWORD',
                                                    usernameVariable: 'BMC_VNODE_USER'),
                                    string(credentialsId: 'vCenter_IP', variable: 'VCENTER_IP'),
                                    string(credentialsId: 'Deployed_OVA_INTERNAL_IP', variable: 'OVA_INTERNAL_IP')
                                ])
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
                                        if (env.USE_PREBUILT_OVA == "true") {
                                            env.OVA_PATH = "$env.OVA_FILE"
                                        } else {
                                            unstash "$OVA_STASH_NAME"
                                        }
                                    
                                        sh '''#!/bin/bash
                                        ./build-config/jobs/FunctionTest/prepare_common.sh
                                        ./build-config/jobs/build_ova/prepare_ova_post_test.sh
                                        '''
                                    } catch(error){
                                        // Clean up test stack
                                        sh '''#!/bin/bash -x
                                        ./build-config/jobs/FunctionTest/cleanup.sh
                                        '''
                                        echo "Caught: ${error}"
                                        error("Preparation of ova post test failed.")
                                    }
                                    function_test.functionTest(test_name, TEST_TYPE, test_group, run_fit_test, run_cit_test, ova_test_stack, extra_hw)
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
    def OVA_TESTS = "${env.OVA_POST_TESTS}"
    function_test.archiveArtifactsToTarget("OVA_POST_TEST", OVA_TESTS, TEST_TYPE)
}

return this
