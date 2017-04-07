#!/bin/bash
set -ex
pushd $WORKSPACE

curl --user $BINTRAY_CREDS -L "$MANIFEST_FILE_URL" -o rackhd-manifest
./on-build-config/build-release-tools/HWIMO-BUILD on-build-config/build-release-tools/application/make_debian_packages.py \
--build-directory b \
--manifest-file  rackhd-manifest \
--sudo-credential SUDO_CREDS \
--parameter-file downstream_file \
--jobs 8 \
--force \
--is-official-release $IS_OFFICIAL_RELEASE \
--bintray-credential BINTRAY_CREDS \
--bintray-subject $BINTRAY_SUBJECT \
--bintray-repo $BINTRAY_REPO


./on-build-config/build-release-tools/HWIMO-BUILD on-build-config/build-release-tools/application/release_debian_packages.py \
--build-directory b/ \
--bintray-credential BINTRAY_CREDS \
--bintray-subject $CI_BINTRAY_SUBJECT \
--bintray-repo $CI_BINTRAY_REPO \
--bintray-component $BINTRAY_COMPONENT \
--bintray-distribution $BINTRAY_DISTRIBUTION \
--bintray-architecture $BINTRAY_ARCHITECTURE

popd
