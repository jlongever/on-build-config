#!/bin/bash -e

######################################
#
# Download static file from deb
#
####################################
downloadOnImagebuilderFromDeb(){
    if [ $# -lt 4 ]; then
        echo "[Error] Wrong usage of $0. Abort "
        exit -1
    fi
    local artifactory_url=${1%/}  #remove the trailing slash
    local deb_version=$2
    local stage_repo=$3
    local local_folder=$4

    # Download the staging on-imagebuilder.deb
    local remote_deb_file_path=${stage_repo}/pool/o
    #the remote deb file name
    local deb_name=on-imagebuilder_${deb_version}_all.deb
    local local_deb_fname=local-on-imaegbuilder-${deb_version}.deb

    echo "[Info] Downloading on-imagebuilder deb , version = $on_imagebuilder_version ... URL: ${artifactory_url}/${remote_deb_file_path}/${deb_name}"

    #Download the deb package to local folder (the URL is senstive to duplicated splash)
    wget -c -t 5 -nv ${artifactory_url}/${remote_deb_file_path}/${deb_name} -O ${local_deb_fname}

    # Extact the deb content into a folder
    if [ "$(which dpkg-deb)" == "" ]; then
         echo $SUDO_PASSWORD |sudo -S apt-get install -y dpkg
    fi

    mkdir -p $local_folder

    #using dpkg-deb -x to extract the deb file
    dpkg-deb -x $local_deb_fname  $local_folder
}


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

STAGE_FOLDER=deb_content
mkdir -p $STAGE_FOLDER

#Download deb
downloadOnImagebuilderFromDeb ${ARTIFACTORY_URL}   ${on_imagebuilder_version}  ${STAGE_REPO_NAME} ${STAGE_FOLDER}


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
