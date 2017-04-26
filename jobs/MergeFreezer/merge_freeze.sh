#!/bin/bash -x
# Gain MergeFreezer control

./build-release-tools/HWIMO-BUILD ./build-release-tools/application/gain_job_control.py \
--jenkins-cred $JENKINS_USER:$JENKINS_PASS \
--sentry $SENTRY \
--job-name $JOB_NAME \
--jenkins-url $JENKINS_URL \
--force $MANUAL 

if [ $? -eq 1 ]; then
    echo "There are manually triggered MergeFreezer, exit."
    exit 0
fi

# Run MergeFreezer
run(){
    ./build-release-tools/HWIMO-BUILD ./build-release-tools/application/merge_freeze.py \
    --ghtoken "$GITHUB_TOKEN" \
    --manifest-file ./build-release-tools/lib/manifest.json \
    --freeze-context "$FREEZE_CONTEXT" \
    --freeze-desc "$FREEZE_DESC" \
    --unfreeze-desc "$UNFREEZE_DESC" \
    --freeze "$FREEZE_OR_UNFREEZE"
}

if [ "$FREEZE_OR_UNFREEZE" == "true" ]; then
    while true; do
        run
    done
elif [ "$FREEZE_OR_UNFREEZE" == "false" ]; then
    run
fi
