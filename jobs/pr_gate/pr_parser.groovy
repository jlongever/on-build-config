node{
    deleteDir()
    withEnv([
        "ghprbPullLink = ${env.ghprbPullLink}",
        "ghprbTargetBranch = ${env.ghprbTargetBranch}"
    ]) {
        def shareMethod
        dir("on-build-config") {
            checkout scm
        }
        try{
            env.stash_manifest_path = "manifest"
            withCredentials([string(credentialsId: 'PULLER_GITHUB_TOKEN_POOL',
                                    variable: 'PULLER_GITHUB_TOKEN_POOL')]) {
                sh '''#!/bin/bash -ex
                ./on-build-config/build-release-tools/HWIMO-BUILD ./on-build-config/build-release-tools/application/pr_parser.py \
                --change-url $ghprbPullLink \
                --target-branch $ghprbTargetBranch \
                --puller-ghtoken-pool "${PULLER_GITHUB_TOKEN_POOL}" \
                --manifest-file-path "${stash_manifest_path}"
                '''
             }
        } finally{
            archiveArtifacts 'manifest'
            stash name: 'manifest', includes: 'manifest'
            env.stash_manifest_name = "manifest"
            env.stash_manifest_path = "manifest"
        }
    }
}
