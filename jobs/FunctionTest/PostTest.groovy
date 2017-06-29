node{
    deleteDir()
    checkout scm
    def shareMethod = load("jobs/ShareMethod.groovy")
    def function_test = load("jobs/FunctionTest/FunctionTest.groovy")
    def ova_post_test = load("jobs/build_ova/ova_post_test.groovy")
    def docker_post_test = load("jobs/build_docker/docker_post_test.groovy")
    def test_branches = [:]

    // vagrant post test
    test_branches["vagrant post test"] = {
        load("jobs/build_vagrant/vagrant_post_test.groovy")
    }
    test_branches += ova_post_test.generateTestBranches(function_test)
    test_branches += docker_post_test.generateTestBranches(function_test)
    if(test_branches.size() > 0){
        try{
            parallel test_branches
        }
        finally{
            ova_post_test.archiveArtifacts(function_test)
            docker_post_test.archiveArtifacts(function_test)
        }
    }
}

