node {
    deleteDir()
    checkout scm
    stage("Launch MergeFreezer"){
        withCredentials([string(credentialsId: 'JENKINSRHD_GITHUB_TOKEN', variable: 'GITHUB_TOKEN'),
                         usernamePassword(credentialsId: '752052b8-c884-4c2a-95ef-04e0f9fa0bc2', 
                             passwordVariable: 'JENKINS_PASS', 
                             usernameVariable: 'JENKINS_USER')]) {

            // Run MergeFreezer
            sh '''#!/bin/bash -x
            ./jobs/MergeFreezer/merge_freeze.sh
            '''
        }
    }
}
