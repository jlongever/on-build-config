#!/bin/bash
set -ex
pushd $WORKSPACE

LOCAL_BUILD_DIR=b
echo "using Artifactory: " $ARTIFACTORY_URL

curl --user $BINTRAY_CREDS -L "$MANIFEST_FILE_URL" -o rackhd-manifest
./on-build-config/build-release-tools/HWIMO-BUILD on-build-config/build-release-tools/application/make_debian_packages.py \
--build-directory $LOCAL_BUILD_DIR \
--manifest-file  rackhd-manifest \
--sudo-credential SUDO_CREDS \
--parameter-file downstream_file \
--jobs 8 \
--force \
--is-official-release $IS_OFFICIAL_RELEASE \
--bintray-credential BINTRAY_CREDS \
--bintray-subject $BINTRAY_SUBJECT \
--bintray-repo $BINTRAY_REPO \
--artifactory-url $ARTIFACTORY_URL \
--artifactory-repo $STAGE_REPO_NAME \
--artifactory-username $ARTIFACTORY_USR \
--artifactory-password $ARTIFACTORY_PWD \


./on-build-config/build-release-tools/HWIMO-BUILD on-build-config/build-release-tools/application/upload_staging_deb_to_artifactory.py \
--build-directory ${LOCAL_BUILD_DIR}/ \
--artifactory-url $ARTIFACTORY_URL \
--artifactory-repo $STAGE_REPO_NAME \
--artifactory-username $ARTIFACTORY_USR \
--artifactory-password $ARTIFACTORY_PWD \
--deb-distribution $DEB_DISTRIBUTION \
--deb-component  $DEB_COMPONENT \
--deb-architecture $DEB_ARCHITECTURE


popd
