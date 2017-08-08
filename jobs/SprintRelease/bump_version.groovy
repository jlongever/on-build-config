node{
    withEnv([
        "tag_name=${tag_name}",
        "JUMP_VERSION=${JUMP_VERSION}",
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
            stage("Bump Version"){
                withEnv(["MANIFEST_FILE_URL=${MANIFEST_FILE_URL}"]){
                    retry(retry_times){
                        timeout(5){
                            sh '''#!/bin/bash -ex
                            # Checkout code according to manifest file
                            curl --user $BINTRAY_USERNAME:$BINTRAY_API_KEY -L "$MANIFEST_FILE_URL" -o rackhd-manifest
                            ./build-config/build-release-tools/HWIMO-BUILD build-config/build-release-tools/application/reprove.py \
                            --manifest rackhd-manifest \
                            --builddir b \
                            --git-credential https://github.com,JENKINSRHD_GITHUB_CREDS \
                            --jobs 8 \
                            --force \
                            checkout
                            '''
                        }
                    }

                    retry(retry_times){
                        timeout(3){
                            sh '''#!/bin/bash -ex
                            # Jump version of repositories which are just checked out.
                            version=`echo $tag_name | grep "[0-9.]*" -o`
                            ./build-config/build-release-tools/HWIMO-BUILD build-config/build-release-tools/application/jump_version.py \
                            --build-dir b \
                            --version $version \
                            --message "release $version" \
                            --publish \
                            --git-credential https://github.com,JENKINSRHD_GITHUB_CREDS
                            '''
                        }
                    }
                }
            }
            stage("Update Manifest"){
                retry(retry_times){
                    timeout(3){
                        sh './build-config/jobs/SprintRelease/update_manifest.sh'
                    }
                }
                // inject properties file as environment variables
                if(fileExists ('downstream_file')) {
                    def props = readProperties file: 'downstream_file';
                    if(props['MANIFEST_FILE_URL']) {
                        env.MANIFEST_FILE_URL = "${props.MANIFEST_FILE_URL}";
                    }
                    else{
                        error("Failed to Update manifest")
                    }
                }
            }
        }
    }
}
