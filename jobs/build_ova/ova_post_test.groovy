node(build_ova_node){
    lock("packer_bri"){
        timestamps{
            withEnv([
                "WORKSPACE=${env.OVA_WORKSPACE}", 
                "IS_OFFICIAL_RELEASE=${env.IS_OFFICIAL_RELEASE}", 
                "RACKHD_VERSION=${env.RACKHD_VERSION}",
                "OS_VER=${env.OS_VER}"]){
            
                def shareMethod
                dir("OVA_Post_Test_JFiles"){
                    checkout scm
                    shareMethod = load("jobs/shareMethod.groovy")
                }

                def url = 'https://github.com/RackHD/on-build-config.git'
                def branch = '*/master'
                def targetDir = 'build-config'
                shareMethod.checkout(url, branch, targetDir)

                withCredentials([
                    usernamePassword(credentialsId: 'OVA_POST_TEST_ESXI_HOST', 
                                     passwordVariable: 'ESXI_HOST_IP_AGAIN', 
                                     usernameVariable: 'ESXI_HOST_IP'),
                    usernamePassword(credentialsId: '00aa0b00-f027-4791-a539-51bf0181172a',
                                     passwordVariable: 'ESXI_PASS',
                                     usernameVariable: 'ESXI_USER'),
                    usernamePassword(credentialsId: 'VCENTER_NT_CREDS', 
                                     passwordVariable: 'VCENTER_NT_PASSWORD', 
                                     usernameVariable: 'VCENTER_NT_USER')]) {

                    timeout(90){
                        sh './OVA_Post_Test_JFiles/jobs/build_ova/ova_post_test.sh'
                    }
                }
            }
        }
    }
}
