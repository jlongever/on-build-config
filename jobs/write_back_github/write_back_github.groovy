node{
    withEnv([
        "stash_manifest_name=${env.stash_manifest_name}",
        "stash_manifest_path=${env.stash_manifest_path}"
        ]){
        deleteDir()
        dir("build-config"){
            checkout scm
        }
        unstash "${stash_manifest_name}"
        withCredentials([string(credentialsId: 'JENKINSRHD_GITHUB_TOKEN', 
                                variable: 'GITHUB_TOKEN')]) {
            if ("${currentBuild.result}" == "null"){
                currentBuild.result = "FAILURE"
            }
            env.status = "${currentBuild.result}"
            sh './build-config/jobs/write_back_github/write_back_github.sh'
        }
    }
}
