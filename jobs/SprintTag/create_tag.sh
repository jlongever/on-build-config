#!/bin/bash
export GITHUB_CREDS=${JENKINSRHD_GITHUB_CREDS}
echo "start to generate manifest for tag"
./build-config/build-release-tools/HWIMO-BUILD build-config/build-release-tools/application/generate_manifest.py \
--branch "$branch" \
--date "$date" \
--timezone "$timezone" \
--builddir b \
--force \
--jobs 8

arrBranch=($(echo $branch | tr "/" "\n"))
slicedBranch=${arrBranch[-1]}
manifest_file=$(find -maxdepth 1 -name "$slicedBranch-[0-9]*")

echo "Start to create tag"
./build-config/build-release-tools/HWIMO-BUILD build-config/build-release-tools/application/reprove.py \
--manifest $manifest_file \
--builddir b \
--tag-name $tag_name \
--git-credential https://github.com,GITHUB_CREDS \
--jobs 8 \
tag

echo "push the manifest of the tag ${tag_name} to bintray"
arrNewTag=($(echo $tag_name | tr "/" "\n"))
new_manifest=${arrNewTag[-1]}

mv $manifest_file $new_manifest
./build-config/build-release-tools/pushToBintray.sh \
--user $BINTRAY_USERNAME \
--api_key $BINTRAY_API_KEY \
--subject $BINTRAY_SUBJECT \
--repo $BINTRAY_REPO \
--package manifest \
--version $new_manifest \
--file_path $new_manifest

MANIFEST_FILE_URL=https://dl.bintray.com/$BINTRAY_SUBJECT/$BINTRAY_REPO/$new_manifest
echo "MANIFEST_FILE_URL=<a href=\"$MANIFEST_FILE_URL\">$new_manifest</a>"
echo "MANIFEST_FILE_URL=$MANIFEST_FILE_URL" > downstream_file

check_file_exist(){
    echo "try to download the manifest"
    max_retry=200
    time=0
    while [ $time -le $max_retry ]
    do
        time=$(($time + 1))
        sleep 10
        if [ $(curl --user $BINTRAY_USERNAME:$BINTRAY_API_KEY --write-out %{http_code} --silent --output /dev/null $MANIFEST_FILE_URL) -eq "200" ]; then
            return 0
        fi
    done
    return 1
}
check_file_exist
