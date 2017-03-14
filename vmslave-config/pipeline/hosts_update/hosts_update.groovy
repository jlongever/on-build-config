def checkout(String url, String branch, String targetDir){
    checkout(
    [$class: 'GitSCM', branches: [[name: branch]],
    extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: targetDir]],
    userRemoteConfigs: [[url: url]]])
}

node('vmslave-config') {
    withEnv([
        "HUDSON_URL=${env.HUDSON_URL}",
        "EXTRA_TEXT=${env.EXTRA_TEXT}"
    ]){
         withCredentials([
                usernamePassword(credentialsId: 'JENKINS_ADMIN',
                                 passwordVariable: 'JENKINS_PASS', 
                                 usernameVariable: 'JENKINS_USER')
        ]) {
            deleteDir()
            checkout(env.GIT_URL, env.GIT_COMMIT, 'rackhd')
            dir('rackhd'){
                sh 'vmslave-config/pipeline/hosts_update/hosts_update.sh'
                stash name: 'hosts', includes: 'hosts'
            }
        }
    }
}