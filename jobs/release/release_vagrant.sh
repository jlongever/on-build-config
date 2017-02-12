#!/bin/bash


set +e
echo "upload vagrant to atlas"
# for test
cd VAGRANT
mv $(ls) $(ls | sed "s/1.1-1/1.1.1/")
cd ..

##########################
# FIXME: temporary disable the release_box, since on sprint regression, it will fail to release old versions.
# sed  -i "s/        self.release_box(atlas_version)//g"  on-build-config/build-release-tools/application/release_to_atlas.py
#########################


./on-build-config/build-release-tools/HWIMO-BUILD on-build-config/build-release-tools/application/release_to_atlas.py \
--build-directory ./VAGRANT/build/packer \
--atlas-url https://atlas.hashicorp.com/api/v1 \
--atlas-creds ${ATLAS_CREDS} \
--atlas-name rackhd \
--is-release $IS_OFFICIAL_RELEASE 

