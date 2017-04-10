node{
    withEnv([
        "stash_manifest_name=${env.stash_manifest_name}",
        "stash_manifest_path=${env.stash_manifest_path}",
        "MANIFEST_FILE_URL=${env.MANIFEST_FILE_URL}"
    ]){
        try{
            deleteDir()
            checkout scm

            def repo_dir = pwd()
            def prgate_unit_test = load("jobs/UnitTest/PRGateUnitTest.groovy")
            if("${stash_manifest_name}" != null && "${stash_manifest_name}" != "null"){
                if("${stash_manifest_path}" != null && "${stash_manifest_path}" != "null"){
                    prgate_unit_test.runTest("${stash_manifest_name}", "${stash_manifest_path}", repo_dir)
                }
                else{
                    sh '''
                    echo "Please provider argument stash_manifest_path if you provided argument stash_manifest_name"
                    exit 1
                    '''
                }
            } else if("${MANIFEST_FILE_URL}" != null && "${MANIFEST_FILE_URL}" != "null"){
                sh 'curl $MANIFEST_FILE_URL -o manifest'
                stash name: "unittest_manifest", includes: "manifest"
                prgate_unit_test.runTest("unittest_manifest", "manifest", repo_dir)
            } else{
                error 'Please provide the manifest url or a stashed manifest'
            }

        }catch(error){
            echo "Caught: ${error}"
            currentBuild.result="FAILURE"
            throw error
        }
    }
}

