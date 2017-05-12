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
                usernamePassword(credentialsId: '752052b8-c884-4c2a-95ef-04e0f9fa0bc2',
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
