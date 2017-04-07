#!/bin/bash -e
set +x
export GITHUB_CREDS=$GITHUB_USERNAME:$GITHUB_PASSWORD
set -x
curl --user $BINTRAY_USERNAME:$BINTRAY_API_KEY -L "$MANIFEST_FILE_URL" -o rackhd-manifest
echo "Create tag to the latest commit of repositories under the build directory"
./build-config/build-release-tools/HWIMO-BUILD build-config/build-release-tools/application/reprove.py \
--manifest rackhd-manifest \
--builddir d \
--tag-name $tag_name \
--git-credential https://github.com,GITHUB_CREDS \
--jobs 8 \
--force \
checkout \
tag
