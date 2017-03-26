node{
    withEnv([
        "tag_name=${tag_name}",
        "IS_OFFICIAL_RELEASE=${env.IS_OFFICIAL_RELEASE}",
        "branch=${env.branch}",
        "date=current",
        "timezone=-0500",
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
            stage("Create Tag"){
                retry(3){
                    timeout(5){
                        sh './build-config/jobs/SprintTag/create_tag.sh'
                    }
                }
            }
	    // inject properties file as environment variables
            if(fileExists ('downstream_file')) {
                def props = readProperties file: 'downstream_file';
                if(props['MANIFEST_FILE_URL']) {
                    env.MANIFEST_FILE_URL = "${props.MANIFEST_FILE_URL}";
                }
            }
	}
    }
}
