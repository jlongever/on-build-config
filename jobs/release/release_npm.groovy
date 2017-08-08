node{
    withEnv([
        "MANIFEST_FILE_URL=${env.MANIFEST_FILE_URL}",
        "IS_OFFICIAL_RELEASE=${env.IS_OFFICIAL_RELEASE}"
        ]) {
        deleteDir()
        dir("build-config"){
            checkout scm
        }
        withCredentials([
            usernameColonPassword(credentialsId: 'a94afe79-82f5-495a-877c-183567c51e0b', 
                                  variable: 'BINTRAY_CREDS'), 
            usernamePassword(credentialsId: '736849f6-ba2c-489d-b5ca-d1b1f4be2252', 
                             passwordVariable: 'NPM_TOKEN', 
                             usernameVariable: 'NPM_REGISTRY')]) {
      
            sh '''#download manifest
            curl --user $BINTRAY_CREDS -L "$MANIFEST_FILE_URL" -o rackhd-manifest

            ./build-config/build-release-tools/HWIMO-BUILD build-config/build-release-tools/application/release_npm_packages.py \
            --build-directory b \
            --manifest-file rackhd-manifest \
            --npm-credential $NPM_REGISTRY,$NPM_TOKEN \
            --jobs 8 \
            --is-official-release $IS_OFFICIAL_RELEASE \
            --force
            '''
        }
    }
}

