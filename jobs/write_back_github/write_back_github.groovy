node{
    withEnv([
        "stash_manifest_name=${env.stash_manifest_name}",
        "stash_manifest_path=${env.stash_manifest_path}"
        ]){
        deleteDir()
        dir("build-config"){
            checkout scm
        }
        unstash "${env.stash_manifest_name}"
        withCredentials([string(credentialsId: 'JENKINSRHD_GITHUB_TOKEN', 
                                variable: 'GITHUB_TOKEN')]) {
            // if previous steps all pass,  $currentBuild.result will be set to "SUCCESS" explictly in pipeline groovy code
            // if Junit plugin found test case error in previous step,  the plugin will set $currentBuild.result  to "Unstable"
            // if previous steps abort with error, the $currentBuild.result will not get chance to be set . so value is "null" here
            // ------
            //Jenkins currentBuild.result| github commit status(https://developer.github.com/v3/repos/statuses/ )
            // null                      | failure
            // failure                   | failure
            // unstable                  | failure
            // success                   | success
            if ("${currentBuild.result}" != "SUCCESS"){
                currentBuild.result = "FAILURE"
            }
            env.status = "${currentBuild.result}"
            sh './build-config/jobs/write_back_github/write_back_github.sh'
        }
    }
}
