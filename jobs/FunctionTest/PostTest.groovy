node{
    deleteDir()
    checkout scm
    def shareMethod = load("jobs/ShareMethod.groovy")
    def function_test = load("jobs/FunctionTest/FunctionTest.groovy")
    def ova_post_test = load("jobs/build_ova/ova_post_test.groovy")
    def docker_post_test = load("jobs/build_docker/docker_post_test.groovy")
    def test_branches = [:]

    echo "111111111111111111111111"
    // vagrant post test
    test_branches["vagrant post test"] = {
        load("jobs/build_vagrant/vagrant_post_test.groovy")
    }
    print test_branches
    test_branches += ova_post_test.generateTestBranches()
    echo "2222222222222222"
    print test_branches
    test_branches += docker_post_test.generateTestBranches()
    echo "3333333333333333333"
    print test_branches
    if(test_branches.size() > 0){
        try{
            parallel test_branches
        }
        finally{
            ova_post_test.archiveArtifacts()
            docker_post_test.archiveArtifacts()           
        }
    }
}

