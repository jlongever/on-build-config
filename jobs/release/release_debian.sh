#!/bin/bash
set -ex
echo "upload debian to bintray"

if [ $IS_OFFICIAL_RELEASE == true ];
then
BINTRAY_COMPONENT=release
fi
echo $BINTRAY_COMPONENT

./on-build-config/build-release-tools//HWIMO-BUILD ./on-build-config/build-release-tools/application/release_debian_packages.py \
--build-directory DEBIAN/ \
--bintray-credential BINTRAY_CREDS \
--bintray-subject $BINTRAY_SUBJECT \
--bintray-repo $BINTRAY_REPO \
--bintray-component $BINTRAY_COMPONENT \
--bintray-distribution $BINTRAY_DISTRIBUTION \
--bintray-architecture $BINTRAY_ARCHITECTURE
