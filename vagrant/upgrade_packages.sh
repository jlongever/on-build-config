#!/bin/bash -x

VERSION_TO_INSTALL="0"

# Determine latest version that is not on the blacklist
get_latest_version () {
    for version in `rmadison $PACKAGE_NAME | awk -F'[|:-]' '{ print $3 }'`; do
	if dpkg --compare-versions $version gt $VERSION_TO_INSTALL; then

            # Determine if this version is on the blacklist
	    version_ok=true
	    for bad_version in $BLACKLIST; do
		if [ $bad_version == $version ]; then
		    version_ok=false
		    break
		fi
	    done
	    if [ $version_ok == true ]; then
		VERSION_TO_INSTALL=$version
	    fi
	fi
    done
}

# Required package for running rmadison
sudo apt-get install liburi-perl

# Update MongoDB
PACKAGE_NAME="mongodb"
BLACKLIST=`cat blacklist_mongo.txt`
get_latest_version
if [ $VERSION_TO_INSTALL == "0" ]; then
    echo "No version found"
    exit 1
fi
# Determine if version is already installed
installed_version=`mongo --version | awk '{ print $4 }'`
if [ $installed_version == $VERSION_TO_INSTALL ]; then
    echo "$VERSION_TO_INSTALL already installed"
    exit 0
fi
sudo service mongod stop
sudo apt-get remove $PACKAGE_NAME* --purge --assume-yes
sudo apt-get autoremove --assume-yes
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' | sudo tee /etc/apt/sources.list.d/mongodb.list
sudo apt-get update
sudo apt-get install --assume-yes mongodb-org=$VERSION_TO_INSTALL mongodb-org-server=$VERSION_TO_INSTALL mongodb-org-shell=$VERSION_TO_INSTALL mongodb-org-mongos=$VERSION_TO_INSTALL mongodb-org-tools=$VERSION_TO_INSTALL
