#!/bin/bash

# Copyright 2016, EMC, Inc.

# set -x

rm -f /var/lib/dhcp/dhchp.leases
touch /var/lib/dhcp/dhcpd.leases
chown root:root /var/lib/dhcp/dhcpd.leases
chmod 666 /var/lib/dhcp/dhcpd.leases

service isc-dhcp-server stop

cd /RackHD/ucs-service
pip install -r requirements.txt
cd /RackHD
mongod &
sleep 1
service rabbitmq-server start
sleep 1
pm2 start /rackhd.yml
dhcpd -f -cf /etc/dhcp/dhcpd.conf -lf /var/lib/dhcp/dhcpd.leases --no-pid
