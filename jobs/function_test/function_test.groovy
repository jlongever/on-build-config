@NonCPS
def printParams() {
  env.getEnvironment().each { name, value -> println "Name: $name -> Value $value" }
}

def TESTS=[:]
TESTS["FIT"]=["TEST_GROUP":"smoke-tests","RUN_FIT_TEST":true,"RUN_CIT_TEST":false]
TESTS["Install Centos 6.5"]=["TEST_GROUP":"centos-6-5-minimal-install.v1.1.test","RUN_FIT_TEST":false,"RUN_CIT_TEST":true]
TESTS["CIT"]=["TEST_GROUP":"smoke-tests","RUN_FIT_TEST":false,"RUN_CIT_TEST":true]
TESTS["Install Ubuntu 14.04"]=["TEST_GROUP":"ubuntu-minimal-install.v1.1.test","RUN_FIT_TEST":false,"RUN_CIT_TEST":true]
TESTS["Install ESXI 6.0"]=["TEST_GROUP":"esxi-6-min-install.v1.1.test","RUN_FIT_TEST":false,"RUN_CIT_TEST":true]

def function_test(String test_name, String node_name, String TEST_GROUP, Boolean RUN_FIT_TEST, Boolean RUN_CIT_TEST){
    node(node_name){
        deleteDir()
        
        dir("on-build-config"){
            checkout scm
        }
        if("${stash_manifest_name}" != null && "${stash_manifest_name}" != "null"){
            unstash "${stash_manifest_name}"
        }
        if("${stash_manifest_path}" != null && "${stash_manifest_path}" != "null"){
            env.MANIFEST_FILE="$stash_manifest_path"
        }
        else if("${MANIFEST_FILE_URL}" != null && "${MANIFEST_FILE_URL}" != "null"){
            sh 'curl $MANIFEST_FILE_URL -o manifest'
            env.MANIFEST_FILE = "manifest"
        }
        else{
            error 'Please provide the manifest url or a stashed manifest'
        }
         
        sh '''#!/bin/bash
        ./on-build-config/build-release-tools/HWIMO-BUILD ./on-build-config/build-release-tools/application/parse_manifest.py \
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

        timestamps{
            withEnv([
                "TEST_GROUP=$TEST_GROUP",
                "RUN_CIT_TEST=$RUN_CIT_TEST",
                "RUN_FIT_TEST=$RUN_FIT_TEST",
                "SKIP_PREP_DEP=false",
                "MANIFEST_FILE=${env.MANIFEST_FILE}",
                "NODE_NAME=${env.NODE_NAME}"]
            ){
                try{
                    timeout(50){
                        sh 'on-build-config/test.sh'
                    }
                    
                } catch(error){
                    throw error
                } finally{
                    sh 'on-build-config/jobs/function_test/cleanup.sh'
                    def artifact_dir = test_name.replaceAll(' ', '-')
                    sh '''#!/bin/bash -ex
                    ./build-config/post-deploy.sh
                    mkdir '''+"$artifact_dir"+'''
                    cp build-deps/*.log '''+"$artifact_dir"+'''
                    cp RackHD/test/*.xml '''+"$artifact_dir"

                    archiveArtifacts "$artifact_dir/*.*"
                    junit 'RackHD/test/*.xml'
                    sh '''#!/bin/bash -ex
                    find RackHD/test/ -name "*.xml" > files.txt
                    files=$( paste -s -d ' ' files.txt )
                    ./on-build-config/build-release-tools/application/parse_test_results.py \
                    --test-result-file "$files"  \
                    --parameters-file downstream_file
                    '''
                    int failure_count = 0
                    int error_count = 0
                    if(fileExists ("downstream_file")) {
                        def props = readProperties file: "downstream_file"
                        failure_count = "${props.failures}".toInteger()
                        error_count = "${props.errors}".toInteger()
                    }
                    if (failure_count > 0 || error_count > 0){
                        currentBuild.result = "SUCCESS"
                        echo "there are failed test cases"
                        sh 'exit 1'
                    }
                }
            }
        }
    }
}


def run_test(TESTS, label_name){
    def test_count = TESTS.size()
    lock(label: label_name, quantity: test_count)
    {
        def test_branches = [:]
        def lock_nodes=org.jenkins.plugins.lockableresources.LockableResourcesManager.class.get().getResourcesFromBuild(currentBuild.getRawBuild())
        test_names = TESTS.keySet() as String[]
        for(int i=0;i<test_count;i++){
            def node_name = lock_nodes[i].getName()
            def test_name = test_names[i]
            def test_group = TESTS[test_name]["TEST_GROUP"]
            def run_fit_test = TESTS[test_name]["RUN_FIT_TEST"]
            def run_cit_test = TESTS[test_name]["RUN_CIT_TEST"]
            test_branches[test_name] = {
                function_test(test_name, node_name, test_group, run_fit_test, run_cit_test)
            }
        }
        parallel test_branches
    }
}

def reserve_resource(label_name){
    int free_count=0
    while(free_count<=0){
        free_count = org.jenkins.plugins.lockableresources.LockableResourcesManager.class.get().getFreeResourceAmount(label_name)
        if(free_count == 0){
            sleep 5
        }
    }
    return free_count    
}

node{
    try{
        withEnv([
            "HTTP_STATIC_FILES=${env.HTTP_STATIC_FILES}",
            "TFTP_STATIC_FILES=${env.TFTP_STATIC_FILES}",
            "API_PACKAGE_LIST=on-http-api1.1 on-http-api2.0 on-http-redfish-1.0",
            "USE_VCOMPUTE=${env.USE_VCOMPUTE}",
            "stash_manifest_name=${env.stash_manifest_name}",
            "stash_manifest_path=${env.stash_manifest_path}",
            "MANIFEST_FILE_URL=${env.MANIFEST_FILE_URL}"
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
                int total = TESTS.size()
                int free_count = 0
                while(free_count < total){
                    free_count = reserve_resource("${env.FUNCTION_TEST_LABEL}")
                }
                run_test(TESTS, "${env.FUNCTION_TEST_LABEL}")
            }
        }
    }catch(error){
        echo "Caught: ${error}"
        currentBuild.result = "FAILURE"
        throw error
   } 
}
