node(build_ova_node){
    lock("packer_bri"){
        timestamps{
            withEnv([
                "WORKSPACE=${env.OVA_WORKSPACE}", 
                "IS_OFFICIAL_RELEASE=${env.IS_OFFICIAL_RELEASE}", 
                "RACKHD_VERSION=${env.RACKHD_VERSION}",
                "OS_VER=${env.OS_VER}"]){
                dir("build-config"){
                    checkout scm
                }

                withCredentials([
                    string(credentialsId: 'OVA_POST_TEST_ESXi_US_IP', variable: 'ESXI_HOST_IP'), 
                    usernamePassword(credentialsId: 'OVA_POST_TEST_ESXi_US_CRED',
                                     passwordVariable: 'ESXI_PASS',
                                     usernameVariable: 'ESXI_USER'),
                    usernamePassword(credentialsId: 'VCENTER_NT_CREDS', 
                                     passwordVariable: 'VCENTER_NT_PASSWORD', 
                                     usernameVariable: 'VCENTER_NT_USER'),
                    string(credentialsId: 'vCenter_IP', variable: 'VCENTER_IP'), 
                    string(credentialsId: 'Deployed_OVA_admin_IP', variable: 'OVA_Admin_IP'), 
                    string(credentialsId: 'Deployed_OVA_admin_GW', variable: 'OVA_Admin_GW'), 
                    string(credentialsId: 'Deployed_OVA_admin_DNS', variable: 'OVA_Admin_DNS'), 
                    string(credentialsId: 'Deployed_OVA_Datastore_US', variable: 'ESXI_DataStore')
                    ]) {
                    timeout(90){
                        sh './build-config/jobs/build_ova/ova_post_test.sh'
                    }
                }
            }
        }
    }
}
