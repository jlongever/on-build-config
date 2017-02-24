node{
    withEnv([
        "tag_name=${tag_name}",
        "JUMP_VERSION=${JUMP_VERSION}",
        "IS_OFFICIAL_RELEASE=${env.IS_OFFICIAL_RELEASE}",
        "branch=${env.branch}",
        "date=${env.date}",
        "timezone=${env.timezone}",
        "BINTRAY_SUBJECT=rackhd",
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
            if(JUMP_VERSION == "true"){
                stage("Jump Version"){
                    sh '''#!/bin/bash -ex
                    export GITHUB_CREDS=${JENKINSRHD_GITHUB_CREDS}
                    ./build-config/build-release-tools/HWIMO-BUILD build-config/build-release-tools/application/generate_manifest.py \
                    --branch "$branch" \
                    --date "$date" \
                    --timezone "$timezone" \
                    --builddir b \
                    --force \
                    --jobs 8

                    version=`echo $tag_name | grep "[0-9.]*" -o`
                    ./build-config/build-release-tools/HWIMO-BUILD build-config/build-release-tools/application/jump_version.py \
                    --build-dir b \
                    --version $version \
                    --message "release $version" \
                    --publish \
                    --git-credential https://github.com,GITHUB_CREDS
                    ''' 
                }
            }

            stage("Create Tag"){
                sh './build-config/jobs/SprintTag/create_tag.sh'
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
