node{
    withEnv([
        "JIRA_SERVER=https://rackhd.atlassian.net"])
    {
        deleteDir()
        dir("build-config"){
            checkout scm
        }
    
        withCredentials([
            usernamePassword(credentialsId: 'JIRA_USER', 
                             passwordVariable: 'JIRA_PASSWORD', 
                             usernameVariable: 'JIRA_USERNAME')
        ]){
            int retry_times = 3
            retry(retry_times){
                sh '''#!/bin/bash -ex
                rm -rf downstream_file
                ./build-config/build-release-tools/HWIMO-BUILD build-config/build-release-tools/application/jira_epic_report.py \
                --jira_server $JIRA_SERVER \
                --username $JIRA_USERNAME \
                --password $JIRA_PASSWORD \
                --parameters-file downstream_file
                '''
            }
            // inject properties file as environment variables
            if(fileExists ('downstream_file')) {
                def props = readProperties file: 'downstream_file';
                int p1_issues_count = Integer.valueOf(props['P1_ISSUES_COUNT'])
                if(p1_issues_count > 0) {
                    error("There are P1 issue in ${env.JIRA_SERVER}")
                }
            }
	}
    }
}
