#!/bin/bash -e
#download manifest
curl --user $BINTRAY_CREDS -L "$MANIFEST_FILE_URL" -o rackhd-manifest
echo using artifactory : $ARTIFACTORY_URL

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

#build static files
pushd ./$CLONE_DIR/on-imagebuilder

# Download the staging on-imagebuilder.deb
echo "[Info] Downloading on-imagebuilder deb , version = $on_imagebuilder_version ..."
BINTRAY_DL_URL=https://dl.bintray.com/rackhd/debian
BINTRAY_DEB_LIST_FNAME=debian_list.html
local_deb_fname=local-on-imaegbuilder-${on_imagebuilder_version}.deb
rm  $BINTRAY_DEB_LIST_FNAME  -f

#Get all the debian package lis on Bintray
wget -c -t 5 -nv $BINTRAY_DL_URL  -O $BINTRAY_DEB_LIST_FNAME

# find out the deb package name , it should be on-imagebuilder_$VERSION_all.deb
deb_name=$(cat $BINTRAY_DEB_LIST_FNAME  |grep -o href=.*\"|sed 's/href=//' | sed 's/"//g'|grep  "on-imagebuilder.*${on_imagebuilder_version}.*.deb$")

#Download the deb package to local folder
wget -c -t 5 -nv ${BINTRAY_DL_URL}/${deb_name} -O ${local_deb_fname}

# Extact the deb content into a folder
if [ "$(which dpkg-deb)" == "" ]; then
     echo $SUDO_PASSWORD |sudo -S apt-get install -y dpkg
 fi

STAGE_FOLDER=deb_content
mkdir -p $STAGE_FOLDER

#using dpkg-deb -x to extract the deb file
dpkg-deb -x $local_deb_fname  $STAGE_FOLDER
common_path=${STAGE_FOLDER}/var/renasar/on-http/static/http/common
pxe_path=${STAGE_FOLDER}/var/renasar/on-tftp/static/tftp/

#create $CLONE_DIR/on-imagebuilder/common & $CLONE_DIR/on-imagebuilder/pxe
#put the microkernel static files into them, so that they can be consumed in later docker-build step
rm -rf common pxe
mkdir common
mkdir pxe
cp $common_path/* common/
cp $pxe_path/* pxe/
echo $SUDO_PASSWORD |sudo -S  chown -R $USER:$USER common
echo $SUDO_PASSWORD |sudo -S  chown -R $USER:$USER pxe
popd


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
