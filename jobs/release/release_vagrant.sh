#!/bin/bash
set +e
echo "upload vagrant to atlas"

./on-build-config/build-release-tools/HWIMO-BUILD on-build-config/build-release-tools/application/release_to_atlas.py \
--build-directory ./VAGRANT/build/packer \
--atlas-url https://atlas.hashicorp.com/api/v1 \
--atlas-creds ${ATLAS_CREDS} \
--atlas-name rackhd \
--is-release $IS_OFFICIAL_RELEASE 

