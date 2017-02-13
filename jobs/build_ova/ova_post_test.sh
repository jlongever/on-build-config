#!/bin/bash +xe

delete_ova() {
    ansible esxi -a "./vm_operation.sh -a delete ${ESXI_HOST_IP} 1 ova-for-post-test"
    if [ $? = 0 ]; then
      echo "Delete ova-for-post-test successfully!"
    fi
}
delete_ova
sleep 10

PACKERDIR="$WORKSPACE/build/packer/"
OVA="$PACKERDIR/rackhd-${OS_VER}-${RACKHD_VERSION}.ova"

bash ./build-config/build-release-tools/post_test.sh \
--type ova \
--adminIP 10.62.59.167 \
--adminGateway 10.62.59.1 \
--adminNetmask 255.255.255.0 \
--adminDNS 10.254.174.10 \
--datastore datastore3-nfs \
--deployName ova-for-post-test \
--ovaFile $OVA \
--vcenterHost 10.62.59.250 \
--ntName ${VCENTER_NT_USER} \
--ntPass ${VCENTER_NT_PASSWORD} \
--esxiHost 10.62.59.114 \
--net "ADMIN"="External Connection" \
--rackhdVersion $RACKHD_VERSION
