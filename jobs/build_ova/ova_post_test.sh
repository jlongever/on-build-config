#!/bin/bash +xe
delete_ova() {
    ansible esxi -a "./vm_operation.sh -a delete ${ESXI_HOST_IP} 1 ova-for-post-test"
    if [ $? = 0 ]; then
      echo "Delete ova-for-post-test successfully!"
    fi
}
echo "Delete old OVA"
delete_ova
sleep 10

PACKERDIR="$WORKSPACE/build/packer/"
OVA="$PACKERDIR/rackhd-${OS_VER}-${RACKHD_VERSION}.ova"

echo "Post Test starts "

bash ./build-config/build-release-tools/post_test.sh \
--type ova \
--adminIP ${OVA_Admin_IP} \
--adminGateway ${OVA_Admin_GW} \
--adminNetmask 255.255.255.0 \
--adminDNS ${OVA_Admin_DNS} \
--datastore ${ESXI_DataStore} \
--deployName ova-for-post-test \
--ovaFile $OVA \
--vcenterHost ${VCENTER_IP} \
--ntName ${VCENTER_NT_USER} \
--ntPass ${VCENTER_NT_PASSWORD} \
--esxiHost ${ESXI_HOST_IP} \
--esxiHostUser ${ESXI_USER} \
--esxiHostPass ${ESXI_PASS} \
--net "ADMIN"="External Connection" \
--rackhdVersion $RACKHD_VERSION
