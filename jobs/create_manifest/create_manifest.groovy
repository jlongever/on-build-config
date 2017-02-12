node(create_manifest_node){
    withEnv([
        "IS_OFFICIAL_RELEASE=${env.IS_OFFICIAL_RELEASE}",
        "branch=${env.branch}",
        "date=${env.date}",
        "timezone=${env.timezone}",
        "BINTRAY_SUBJECT=pengtian0",
        "BINTRAY_REPO=binary"]){

        deleteDir()

        def shareMethod
        dir("Create_Manifest_JFiles"){
            checkout scm
            shareMethod = load("jobs/shareMethod.groovy")
        }
        def url = "https://github.com/PengTian0/on-build-config.git"
        def branch = "*/feature/test-pipeline2"
        def targetDir = "on-build-config"
        shareMethod.checkout(url, branch, targetDir)

        withCredentials([
            usernamePassword(credentialsId: 'a94afe79-82f5-495a-877c-183567c51e0b', 
            passwordVariable: 'BINTRAY_API_KEY', 
            usernameVariable: 'BINTRAY_USERNAME')
            ]){
            sh './Create_Manifest_JFiles/jobs/create_manifest/create_manifest.sh'
        }
        // inject properties file as environment variables
        if(fileExists ('downstream_file')) {

            def props = readProperties file: 'downstream_file'

            if(props['MANIFEST_FILE_URL']) {
                env.MANIFEST_FILE_URL = "${props.MANIFEST_FILE_URL}"
            }
            else{
                error("Failed because the manifest file url is not generated")
            }
        }
    }
}

