#!/bin/bash -e
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

on_imagebuilder_version=$( ./build-config/build-release-tools/HWIMO-BUILD ./build-config/build-release-tools/application/version_generator.py \
--repo-dir ./$CLONE_DIR/on-imagebuilder \
--is-official-release $IS_OFFICIAL_RELEASE )

common_path=/var/renasar/on-http/static/http/common
pxe_path=/var/renasar/on-tftp/static/tftp

echo $SUDO_PASSWORD |sudo -S rm -rf /etc/apt/sources.list.d/rackhd.source.list
echo "deb https://dl.bintray.com/$CI_BINTRAY_SUBJECT/debian trusty main" | sudo tee -a /etc/apt/sources.list.d/rackhd.source.list
echo $SUDO_PASSWORD |sudo -S apt-get update
echo $SUDO_PASSWORD |sudo -S apt-get --yes --force-yes remove on-imagebuilder
echo $SUDO_PASSWORD |sudo -S apt-get --yes --force-yes install on-imagebuilder=$on_imagebuilder_version

#build static files
pushd ./$CLONE_DIR/on-imagebuilder
rm -rf common pxe
mkdir common
mkdir pxe
cp $common_path/* common/
cp $pxe_path/* pxe/
sudo chown -R $USER:$USER common
sudo chown -R $USER:$USER pxe
popd

echo $SUDO_PASSWORD |sudo -S apt-get --yes --force-yes remove on-imagebuilder

#docker images build
pushd build-config/build-release-tools/
./docker_build.sh $WORKSPACE/$CLONE_DIR $IS_OFFICIAL_RELEASE
cp $WORKSPACE/$CLONE_DIR/build_record $WORKSPACE
popd

# save docker image to tar
image_list=`cat $WORKSPACE/$CLONE_DIR/build_record | xargs`

docker save -o rackhd_docker_images.tar $image_list

# copy build_record to current directory for stash
cp $WORKSPACE/$CLONE_DIR/build_record .
