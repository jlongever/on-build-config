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
                def test_branches = [:]
                for(int i=0; i<repos.size; i++){
                    def repo_name = repos.get(i)
                    def node_name = "vmslave${i+18}"
                    if(repos.size==1){
                        Random random = new Random();
                        int randomNumber = random.nextInt(25 + 1 - 10) + 10;
                        node_name = "vmslave${randomNumber}"
                    }
                    test_branches["${repo_name}"] = {
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
                parallel test_branches
            }catch(error){
                echo "Caught: ${error}"
                currentBuild.result="FAILURE"
                throw error
            }
        }
    }
}

