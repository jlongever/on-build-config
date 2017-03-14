def checkout(String url, String branch, String targetDir){
    checkout(
    [$class: 'GitSCM', branches: [[name: branch]],
    extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: targetDir]],
    userRemoteConfigs: [[url: url]]])
}

node('vmslave-config') {
    withEnv([
        "GIT_PREVIOUS_COMMIT=${env.GIT_PREVIOUS_COMMIT}",
        "SOURCES_LIST_URL=${env.SOURCES_LIST_URL}",
        "VAGRANT_DEB=${env.VAGRANT_DEB}",
        "VIRTUALBOX_DEB=${env.VIRTUALBOX_DEB}",
        "OVFTOOL_BUNDLE=${env.OVFTOOL_BUNDLE}",
        "ISOFARM_PATH=${env.ISOFARM_PATH}",
        "ISOFARM_SRC=${env.ISOFARM_SRC}",
        "ISOFARM_FSTYPE=${env.ISOFARM_FSTYPE}",
        "ISOFARM_MOUNT_OPTS=${env.ISOFARM_MOUNT_OPTS}",
        "ANSIBLE_HOSTS=${env.ANSIBLE_HOSTS}",
        "RE_CONFIG=${env.RE_CONFIG}",
    ]){
        deleteDir()
        checkout(env.GIT_URL, env.GIT_COMMIT, 'rackhd')
        dir('rackhd'){
            unstash "hosts"
            sh 'vmslave-config/pipeline/vmslave_config/vmslave_config.sh'
        }
    }

}