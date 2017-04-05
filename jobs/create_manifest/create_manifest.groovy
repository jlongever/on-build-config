node{
    withEnv([
        "IS_OFFICIAL_RELEASE=${env.IS_OFFICIAL_RELEASE}",
        "branch=${env.branch}",
        "date=${env.date}",
        "timezone=${env.timezone}",
        "BINTRAY_SUBJECT=rackhd",
        "BINTRAY_REPO=binary"]){
        deleteDir()
        dir("on-build-config"){
            checkout scm
        }
        withCredentials([
            usernamePassword(credentialsId: 'a94afe79-82f5-495a-877c-183567c51e0b', 
            passwordVariable: 'BINTRAY_API_KEY', 
            usernameVariable: 'BINTRAY_USERNAME')
            ]){
            sh './on-build-config/jobs/create_manifest/create_manifest.sh'
        }
        // inject properties file as environment variables
        if(fileExists ('downstream_file')) {
            def props = readProperties file: 'downstream_file'
            if(props['MANIFEST_FILE_URL']) {
                env.MANIFEST_FILE_URL = "${props.MANIFEST_FILE_URL}"
                env.manifest_name = "${props.manifest_name}"
            }
            else{
                error("Failed because the manifest file url is not generated")
            }
        }

        stash name: "manifest", includes: "${env.manifest_name}"
        env.stash_manifest_name = 'manifest'
        env.stash_manifest_path = "${env.manifest_name}"
    }
}

