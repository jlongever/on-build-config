#!/bin/bash +xe

# OVA can connect to external network through two way.
#   1. There's a vSwitch connected to external network and has dhcp server.
#      ova can get IP by DHCP, ${External_vSwitch} is the vSwitch name.
#      so before you set External_vSwitch make sure it can connect to external net and has dhcp server.
#   2. Gateway, connect to external net through $OVA_NET_INTERFACE(eth1) with $OVA_GATEWAY IP

set -x

# If using a passed in ova file from an external http server and bypassing ova build,
# use the path as is, else get the path via ls
if [[ "${OVA_PATH}" == "http"* ]]; then
    OVA="${OVA_PATH}"
else
    OVA=`ls ${OVA_PATH}`
fi

echo "Post Test starts "

deployOva() {
    if [ -n "${External_vSwitch}" ]; then
      echo yes | ovftool \
      --overwrite --powerOffTarget --powerOn --skipManifestCheck \
      --net:"ADMIN=${External_vSwitch}"\
      --net:"CONTROL=${NODE_NAME}-switch" \
      --datastore=${DATASTORE} \
      --name=${NODE_NAME}-ova-for-post-test \
      ${OVA} \
      "vi://${ESXI_USER}:${ESXI_PASS}@${ESXI_HOST}"
    else
      echo yes | ovftool \
      --overwrite --powerOffTarget --powerOn --skipManifestCheck \
      --net:"CONTROL=${NODE_NAME}-switch" \
      --datastore=${DATASTORE} \
      --name=${NODE_NAME}-ova-for-post-test \
      ${OVA} \
      "vi://${ESXI_USER}:${ESXI_PASS}@${ESXI_HOST}"
    fi

    if [ $? = 0 ]; then
        echo "[Info] Deploy OVA successfully".
    else
        echo "[Error] Deploy OVA failed."
        exit 3
    fi
    # OVA_INTERNAL_IP, eth1 IP of ova
    ssh-keygen -f "$HOME/.ssh/known_hosts" -R $OVA_INTERNAL_IP
}

waitForAPI() {
  service_normal_sentence="No auth token"
  timeout=0
  maxto=60
  set +e
  url=http://$OVA_INTERNAL_IP:8080/api/2.0/nodes
  while [ ${timeout} != ${maxto} ]; do
    api_test_result=`curl ${url}`
    echo $api_test_result | grep "$service_normal_sentence" > /dev/null  2>&1
    if [ $? = 0 ]; then
      echo "[Debug] successful.        in this retry time: OVA ansible returns: $api_test_result"
      break
    fi
    sleep 10
    timeout=`expr ${timeout} + 1`
  done
  set -e
  if [ ${timeout} == ${maxto} ]; then
    echo "Timed out waiting for RackHD API service (duration=`expr $maxto \* 10`s)."
    exit 1
  fi
}

configOVA() {
  # config the OVA for post test
  pushd ${WORKSPACE}/build-config/jobs/build_ova/ansible
    echo "ova-post-test ansible_host=$OVA_INTERNAL_IP ansible_user=$OVA_USER ansible_ssh_pass=$OVA_PASSWORD ansible_become_pass=$OVA_PASSWORD" > hosts
    cp -f ${WORKSPACE}/build-config/vagrant/config/mongo/config.json .
    if [ -z "${External_vSwitch}" ]; then
      ansible-playbook -i hosts main.yml --extra-vars "ova_gateway=$OVA_GATEWAY ova_net_interface=$OVA_NET_INTERFACE" --tags "config-gateway"
    fi
    ansible-playbook -i hosts main.yml --tags "before-test"
  popd
}

deployOva
waitForAPI
configOVA


echo "Finished preparation for ova post smoke test"
