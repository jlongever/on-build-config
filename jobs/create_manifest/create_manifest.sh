#!/bin/bash
set -ex
pushd $WORKSPACE
./on-build-config/build-release-tools/HWIMO-BUILD on-build-config/build-release-tools/application/generate_manifest.py \
--branch "$branch" \
--date "$date" \
--timezone "$timezone" \
--builddir b \
--force \
--jobs 8

arrBranch=($(echo $branch | tr "/" "\n"))
slicedBranch=${arrBranch[-1]}
manifest_name=$(find -maxdepth 1 -name "$slicedBranch-[0-9]*" -printf "%f\n")

./on-build-config/build-release-tools/pushToBintray.sh \
--user $BINTRAY_USERNAME \
--api_key $BINTRAY_API_KEY \
--subject $BINTRAY_SUBJECT \
--repo $BINTRAY_REPO \
--package manifest \
--version $manifest_name \
--file_path $branch-*

MANIFEST_FILE_URL=https://dl.bintray.com/$BINTRAY_SUBJECT/$BINTRAY_REPO/$manifest_name
echo "MANIFEST_FILE_URL=<a href=\"$MANIFEST_FILE_URL\">$manifest_name</a>"
echo "MANIFEST_FILE_URL=$MANIFEST_FILE_URL" >> downstream_file
echo "manifest_name=$manifest_name" >> downstream_file
check_file_exist(){
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

popd
