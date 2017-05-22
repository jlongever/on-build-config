node(){
    timestamps{
        withEnv([
            "IS_OFFICIAL_RELEASE=${env.IS_OFFICIAL_RELEASE}", 
            "RACKHD_VERSION=${env.RACKHD_VERSION}",
            "OS_VER=${env.OS_VER}",
            "OVA_GATEWAY=${env.OVA_GATEWAY}",
            "OVA_NET_INTERFACE=${env.OVA_NET_INTERFACE}"]){
            deleteDir()
            checkout scm
            def function_test = load("jobs/FunctionTest/FunctionTest.groovy")
            def repo_dir = pwd()
            def TESTS = "${env.OVA_POST_TESTS}"
            def test_type = "ova"
            try{
                withCredentials([
                    usernamePassword(credentialsId: 'OVA_CREDS', 
                                        passwordVariable: 'OVA_PASSWORD', 
                                        usernameVariable: 'OVA_USER'),
                    string(credentialsId: 'vCenter_IP', variable: 'VCENTER_IP'), 
                    string(credentialsId: 'Deployed_OVA_INTERNAL_IP', variable: 'OVA_INTERNAL_IP')
                    ]) {
                    // Start to run test
                    def OVA_STASH_NAME = "${env.OVA_STASH_NAME}"
                    def OVA_STASH_PATH = "${env.OVA_PATH}"
                    function_test.ovaPostTest(TESTS, OVA_STASH_NAME, OVA_STASH_PATH, repo_dir, test_type)
                }
            }finally{
                function_test.archiveArtifactsToTarget("OVA_POST_TEST", TESTS, test_type)
            }
        }
    }
}
