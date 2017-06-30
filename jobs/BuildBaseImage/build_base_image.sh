#!/bin/bash -x

pushd $WORKSPACE/on-build-config/jobs/BuildBaseImage/base_docker
echo $SUDO_PASSWORD |sudo -S docker build -t rackhd/pipeline .
popd
pushd $WORKSPACE
echo $SUDO_PASSWORD |sudo -S docker save -o rackhd_pipeline_docker.tar rackhd/pipeline
echo $SUDO_PASSWORD |sudo -S chown $USER:$USER rackhd_pipeline_docker.tar
popd
