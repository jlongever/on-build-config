def function_test(String test_name, String label_name, String TEST_GROUP, Boolean RUN_FIT_TEST, Boolean RUN_CIT_TEST, ArrayList<String> used_resources){
    def shareMethod = load("jobs/shareMethod.groovy")
    lock(label:label_name,quantity:1){
        // The locked resources of the build
        def lock_resources=org.jenkins.plugins.lockableresources.LockableResourcesManager.class.get().getResourcesFromBuild(currentBuild.getRawBuild())
        // The locked resources of this step
        resources = shareMethod.getLockedResourceName(lock_resources,label_name)
        def available_resources = resources - used_resources
        if(available_resources.size > 0){
            used_resources.add(available_resources[0])
            node_name = available_resources[0]
        }
        else{
            sh '''
            echo "There is no available resources for'''+"$label_name"+'''
            exit 1
            '''
        }
        node(node_name){
            deleteDir()
            dir("on-build-config"){
                checkout scm
            }
            // Get the manifest file
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
         
            // If the manifest file contains PR of on-http and RackHD, 
            // set the environment variable MODIFY_API_PACKAGE as true
            // The test.sh script will install api package according to API_PACKAGE_LIST
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
                    "NODE_NAME=${env.NODE_NAME}",
                    "PYTHON_REPOS=ucs-service"]
                ){
                    try{
                        timeout(60){
                            sh '''
                            ./on-build-config/jobs/function_test/prepare.sh 
                            ./build-config/test.sh
                            '''
                        }
                    } catch(error){
                        throw error
                    } finally{
                        
                        def artifact_dir = test_name.replaceAll(' ', '-')
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
                        archiveArtifacts "$artifact_dir/*.*"

                        sh '''#!/bin/bash -x
                        ./build-config/jobs/function_test/cleanup.sh
                        find RackHD/test/ -maxdepth 1 -name "*.xml" > files.txt
                        files=$( paste -s -d ' ' files.txt )
                        if [ -z "$files" ];then
                            echo "No test result files generated, maybe it's aborted"
                            exit 1
                        else
                            ./build-config/build-release-tools/application/parse_test_results.py \
                            --test-result-file "$files"  \
                            --parameters-file downstream_file
                        fi
                        '''

                        junit 'RackHD/test/*.xml'
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
}

def run_test(RUN_TESTS){
    // Run test in parallel
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
            function_test(test_name,label_name,test_group, run_fit_test, run_cit_test, used_resources)
        }
    }
    if(test_branches.size() > 0){
        parallel test_branches
    }
}


node{
    deleteDir()
    checkout scm
    try{
        withEnv([
            "HTTP_STATIC_FILES=${env.HTTP_STATIC_FILES}",
            "TFTP_STATIC_FILES=${env.TFTP_STATIC_FILES}",
            "API_PACKAGE_LIST=on-http-api2.0 on-http-redfish-1.0",
            "USE_VCOMPUTE=${env.USE_VCOMPUTE}",
            "stash_manifest_name=${env.stash_manifest_name}",
            "stash_manifest_path=${env.stash_manifest_path}",
            "MANIFEST_FILE_URL=${env.MANIFEST_FILE_URL}",
            "TESTS=${env.TESTS}"
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

                def ALL_TESTS=[:]
                ALL_TESTS["FIT"]=["TEST_GROUP":"smoke-tests","RUN_FIT_TEST":true,"RUN_CIT_TEST":false,"label":"smoke_test"]
                ALL_TESTS["CIT"]=["TEST_GROUP":"smoke-tests","RUN_FIT_TEST":false,"RUN_CIT_TEST":true,"label":"smoke_test"]
                ALL_TESTS["Install Ubuntu 14.04"]=["TEST_GROUP":"ubuntu-minimal-install.v2.0.test","RUN_FIT_TEST":false,"RUN_CIT_TEST":true,"label":"os_install"]
                ALL_TESTS["Install ESXI 6.0"]=["TEST_GROUP":"esxi-6-min-install.v2.0.test","RUN_FIT_TEST":false,"RUN_CIT_TEST":true,"label":"os_install"]
                ALL_TESTS["Install Centos 6.5"]=["TEST_GROUP":"centos-6-5-minimal-install.v2.0.test","RUN_FIT_TEST":false,"RUN_CIT_TEST":true,"label":"os_install"]

                def RUN_TESTS=[:]
                // TESTS is a checkbox parameter. 
                // Its value is a string looks like: 
                // CIT,FIT,Install Ubuntu 14.04,Install ESXI 6.0,Install Centos 6.5
                List tests = Arrays.asList(TESTS.split(','))
                for(int i=0;i<tests.size();i++){
                    RUN_TESTS[tests[i]]=ALL_TESTS[tests[i]]
                }
                run_test(RUN_TESTS)
            }
        }
    }catch(error){
        echo "Caught: ${error}"
        currentBuild.result = "FAILURE"
        throw error
   } 
}
