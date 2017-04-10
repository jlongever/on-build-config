def unit_test(String repo_name, String label_name, ArrayList<String> used_resource){
    def shareMethod = load("build-config/jobs/shareMethod.groovy")
    def node_name=""
    lock(label:label_name,quantity:1){
        def lock_resources=org.jenkins.plugins.lockableresources.LockableResourcesManager.class.get().getResourcesFromBuild(currentBuild.getRawBuild())
        resources_name = shareMethod.getLockedResourceName(lock_resources,label_name)
        def available_resources = resources_name - used_resource
        if(available_resources.size > 0){
            used_resource.add(available_resources[0])
            node_name = available_resources[0]
        }
        node(node_name){
            deleteDir()
            dir("build-config"){
                checkout scm
            }
            unstash 'unittest_manifest'
            timeout(15){
                try{
                    sh "./build-config/jobs/unit_test/unit_test.sh ${repo_name}"
                } catch(error){
                    throw error
                } finally{
                    archiveArtifacts 'xunit-reports/*.xml'
                    junit 'xunit-reports/'+"${repo_name}.xml"

                    sh '''
                    ./build-config/build-release-tools/application/parse_test_results.py \
                    --test-result-file xunit-reports/'''+"${repo_name}"+'''.xml  \
                    --parameters-file downstream_file
                    '''
                    int failure_count = 0
                    if(fileExists ("downstream_file")) {
                        def props = readProperties file: "downstream_file"
                        failure_count = "${props.failures}".toInteger()
                    }
                    if (failure_count > 0){
                        currentBuild.result = "SUCCESS"
                        sh 'exit 1'
                    }
                }
            }
        }
    }
}

node{
    timestamps{
        withEnv([
            "stash_manifest_name=${env.stash_manifest_name}",
            "stash_manifest_path=${env.stash_manifest_path}",
            "MANIFEST_FILE_URL=${env.MANIFEST_FILE_URL}"
            ]){
            try{
                deleteDir()
                env.current_workspace = pwd()
                dir("build-config"){
                    checkout scm 
                }
                if("${stash_manifest_name}" != null && "${stash_manifest_name}" != "null"){
                    unstash "${stash_manifest_name}"
                }
                if("${stash_manifest_path}" != null && "${stash_manifest_path}" != "null"){
                    env.MANIFEST_FILE_PATH = "$stash_manifest_path"
                } else if("${MANIFEST_FILE_URL}" != null && "${MANIFEST_FILE_URL}" != "null"){
                    sh 'curl $MANIFEST_FILE_URL -o manifest'
                    env.MANIFEST_FILE_PATH = "manifest"
                } else{
                    error 'Please provide the manifest url or a stashed manifest'
                }

                sh '''#!/bin/bash
                ./build-config/build-release-tools/HWIMO-BUILD ./build-config/build-release-tools/application/parse_manifest.py \
                --manifest-file $MANIFEST_FILE_PATH \
                --parameters-file downstream_file
                '''
                env.REPOS_NEED_UNIT_TEST = ""
                if(fileExists ('downstream_file')) {
                    def props = readProperties file: 'downstream_file'
                    if(props['REPOS_NEED_UNIT_TEST']) {
                        env.REPOS_NEED_UNIT_TEST = "${props.REPOS_NEED_UNIT_TEST}"
                    }
                }
                stash name: "unittest_manifest", includes: "${MANIFEST_FILE_PATH}"
                def repos = env.REPOS_NEED_UNIT_TEST.tokenize(',')
                def used_resource=[]
                def test_branches = [:]
                for(int i=0; i<repos.size; i++){
                    def repo_name = repos.get(i)
                    test_branches["${repo_name}"] = {
                        unit_test(repo_name, "unittest", used_resource)   
                    }
                }
                if(test_branches.size() > 0){
                    parallel test_branches
                }
            }catch(error){
                echo "Caught: ${error}"
                currentBuild.result="FAILURE"
                throw error
            }
        }
    }
}

