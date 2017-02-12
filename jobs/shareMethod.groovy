
def checkout(String url, String branch, String targetDir){

        checkout(
        [$class: 'GitSCM', branches: [[name: branch]],
        extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: targetDir]],
        userRemoteConfigs: [[url: url]]])
    
}



def checkout(String url, String branch){

        checkout(
        [$class: 'GitSCM', branches: [[name: branch]],
        userRemoteConfigs: [[url: url]]])

}

def checkout(String url){
    checkout(url, "master")
}

return this
