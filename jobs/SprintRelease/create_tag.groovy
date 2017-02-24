node{
    withEnv([
        "tag_name=${tag_name}",
        "JUMP_VERSION=${JUMP_VERSION}",
        "MANIFEST_FILE_URL=${MANIFEST_FILE_URL}",
        "IS_OFFICIAL_RELEASE=${env.IS_OFFICIAL_RELEASE}",
        "GITHUB_USERNAME=${env.GITHUB_USERNAME}",
        "GITHUB_PASSWORD=${env.GITHUB_PASSWORD}",
        "BINTRAY_SUBJECT=rackhd",
        "BINTRAY_REPO=binary"])
    {
        deleteDir()
        dir("build-config"){
            checkout scm
        }
    
        withCredentials([
            usernamePassword(credentialsId: 'a94afe79-82f5-495a-877c-183567c51e0b', 
                             passwordVariable: 'BINTRAY_API_KEY', 
                             usernameVariable: 'BINTRAY_USERNAME')
        ]){

            if(JUMP_VERSION == "true"){
                stage("Jump Version"){
                    sh '''#!/bin/bash -e
                    export GITHUB_CREDS=$GITHUB_USERNAME:$GITHUB_PASSWORD
                    
                    curl --user $BINTRAY_USERNAME:$BINTRAY_API_KEY -L "$MANIFEST_FILE_URL" -o rackhd-manifest
                    ./build-config/build-release-tools/HWIMO-BUILD build-config/build-release-tools/application/reprove.py \
                    --manifest rackhd-manifest \
                    --builddir b \
                    --git-credential https://github.com,GITHUB_CREDS \
                    --jobs 8 \
                    --force \
                    checkout

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
                sh './build-config/jobs/SprintRelease/create_tag.sh'
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
