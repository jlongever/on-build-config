node{
    timestamps{
            checkout scm
            def function_test = load("jobs/FunctionTest/FunctionTest.groovy")
            def repo_dir = pwd()
            def TESTS = "${env.DOCKER_POST_TESTS}"
            def test_type = "docker"
            try {
                withCredentials([
                    usernamePassword(credentialsId: 'ff7ab8d2-e678-41ef-a46b-dd0e780030e1',
                                    passwordVariable: 'SUDO_PASSWORD',
                                    usernameVariable: 'SUDO_USER')]
                ){
                    def DOCKER_STASH_NAME = "${env.DOCKER_STASH_NAME}"
                    def DOCKER_STASH_PATH = "${env.DOCKER_STASH_PATH}"
                    def DOCKER_RECORD_STASH_PATH = "${env.DOCKER_RECORD_STASH_PATH}"
                    function_test.dockerPostTest(TESTS, DOCKER_STASH_NAME, DOCKER_STASH_PATH, DOCKER_RECORD_STASH_PATH, repo_dir, test_type)
                }
            } catch(error){
                echo "Caught: ${error}"    
                currentBuild.result = "FAILURE"
            } finally{
                function_test.archiveArtifactsToTarget("DOCKER_POST_SMOKE_TEST", TESTS, test_type)
            }
    }
}
