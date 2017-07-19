#!/bin/bash
set -e
# Environmental requirement:
# docker service running and docker have already logged with Rackhd Dockerhub ID,
#     cmd 'docker login', if not logged then can't push images to dockerhub
cd DOCKER
docker load -i $DOCKER_STASH_PATH
docker login -u $DOCKERHUB_USER -p $DOCKERHUB_PASS

while read -r LINE; do
        echo $LINE
        for repo_tag in $LINE; do
                echo "Pushing rackhd/$repo_tag"
        docker push $repo_tag
        if [ $? != 0 ]; then
                echo "Failed to push rackhd/$repo_tag"
            exit 1
        fi
    done
done < $DOCKER_RECORD_STASH_PATH

# Clean UP. (was in Jenkins job post-build, avoid failure impacts build status.)
set +e
set -x

clean_up(){
    # parameter : the images keyword to be delete
    keyword=$1
    images=`docker images | grep ${keyword} | awk '{print $3}' | sort | uniq`
    if [ -n "$images" ]; then
        docker rmi -f $images
    fi
}

clean_running_containers() {
    local containers=$(docker ps -a -q)
    if [ "$containers" != "" ]; then
        echo "Clean Up containers : " ${containers}
        docker stop ${containers}
        docker rm  ${containers}
    fi
}


echo "Show local docker images"
docker ps
docker images
echo "Stop & rm all docker running containers " 
clean_running_containers
echo "Clean Up all docker images in local repo"
clean_up none
# clean images by order, on-core should be last one because others depends on it
clean_up on-taskgraph
clean_up on-http
clean_up on-tftp
clean_up on-dhcp-proxy
clean_up on-syslog
clean_up on-tasks
clean_up files
clean_up isc-dhcp-server
clean_up on-wss
clean_up on-statsd
clean_up on-core
clean_up rackhd

echo "clean up /var/lib/docker/volumes"
docker volume ls -qf dangling=true | xargs -r docker volume rm

docker logout
echo "docker logout."

exit 0 # this is a workaround. to avoid the cleanup failure makes whole workflow fail.don't worry, the set -e will ensure failure captured for necessary steps(those lines before set +e)
