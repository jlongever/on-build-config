#!/bin/bash
set -x
virtualenv --clear host_update_env
source host_update_env/bin/activate
pip install python-jenkins
./vmslave-config/pipeline/hosts_update/hosts_update.py \
--jenkins-user ${JENKINS_USER} \
--jenkins-pass ${JENKINS_PASS} \
--jenkins-url ${HUDSON_URL} \
--extra-text "${EXTRA_TEXT}" \
--output-path ./hosts
