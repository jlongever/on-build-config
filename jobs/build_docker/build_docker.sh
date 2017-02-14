#!/bin/bash

pwd

#download manifest
curl --user $BINTRAY_CREDS -L "$MANIFEST_FILE_URL" -o rackhd-manifest

#clone
./build-config/build-release-tools/HWIMO-BUILD ./build-config/build-release-tools/application/reprove.py \
  --manifest rackhd-manifest \
  --builddir ./$CLONE_DIR \
  --jobs 8 \
  --force \
  checkout \
  packagerefs-commit

rsync -r ./$CLONE_DIR/RackHD/ ./build/

#build static files
pushd ./$CLONE_DIR/on-imagebuilder
sudo ./build_all.sh

#copy to on-imagebuilder folder for docker build
output_path=/tmp/on-imagebuilder
rm -rf common pxe
mkdir common
mkdir pxe
sudo chmod 644 $output_path/builds/*
sudo chmod 644 $output_path/ipxe/*
sudo chmod 644 $output_path/syslinux/*
cp $output_path/builds/* common/
cp $output_path/syslinux/* pxe/
cp $output_path/ipxe/* pxe/
sudo chown -R $USER:$USER common
sudo chown -R $USER:$USER pxe

popd

#docker images build
cd build-config/build-release-tools/
./docker_build.sh $WORKSPACE/$CLONE_DIR $IS_OFFICIAL_RELEASE
mv $WORKSPACE/$CLONE_DIR/build_record $WORKSPACE

