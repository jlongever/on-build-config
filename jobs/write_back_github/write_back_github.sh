#!/bin/bash 

set -x
pushd $WORKSPACE
build_status="${status}"

if [ "${build_status}" != "SUCCESS" ]; then
    ./build-config/build-release-tools/HWIMO-BUILD ./build-config/build-release-tools/application/post-result.py \
    --manifest_file "${stash_manifest_path}" \
    --jenkins_url "${JENKINS_URL}" \
    --build_url "${BUILD_URL}" \
    --public_jenkins_url "http://147.178.202.18/" \
    --ghtoken ${GITHUB_TOKEN}
fi

./build-config/build-release-tools/HWIMO-BUILD ./build-config/build-release-tools/application/commit_status_setter.py \
--manifest "${stash_manifest_path}" \
--build-url "${BUILD_URL}" \
--public-jenkins-url "http://147.178.202.18/" \
--status "${build_status,,}" \
--ghtoken ${GITHUB_TOKEN}
popd
