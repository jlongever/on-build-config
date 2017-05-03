node{
    withEnv([
        "tag_name=${tag_name}",
        "MANIFEST_FILE_URL=${env.MANIFEST_FILE_URL}",
        "BINTRAY_SUBJECT=${env.BINTRAY_SUBJECT}",
        "BINTRAY_REPO=binary"])
    {
        deleteDir()
        dir("build-config"){
            checkout scm
        }
    
        withCredentials([
            usernameColonPassword(credentialsId: 'GITHUB_USER_PASSWORD_OF_JENKINSRHD',
                                  variable: 'JENKINSRHD_GITHUB_CREDS'),
            usernamePassword(credentialsId: 'a94afe79-82f5-495a-877c-183567c51e0b', 
                             passwordVariable: 'BINTRAY_API_KEY', 
                             usernameVariable: 'BINTRAY_USERNAME')
        ]){
            int retry_times = 3
            stage("Create Tag"){
                retry(retry_times){
                    timeout(5){
                        sh './build-config/jobs/SprintRelease/create_tag.sh'
                    }
                }
            }
	}
    }
}
