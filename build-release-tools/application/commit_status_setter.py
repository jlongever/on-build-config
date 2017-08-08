#!/usr/bin/env python

import sys
import argparse
import os
from github import Github
from manifest import Manifest
from urlparse import urlparse
import time

# jenkins-url is not suggested for our internal Jenkins
def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest",
                        help="manifest file path",
                        required=True,
                        action="store")
    parser.add_argument("--build-url",
                        help="URL of this build",
                        action="store")
    parser.add_argument("--public-jenkins-url",
                        help="The url of the public jenkins, required if build-url not None.",
                        action="store")
    parser.add_argument("--status",
                        help="The status this build, success, failure, pending.",
                        required=True,
                        action="store")
    parser.add_argument("--ghtoken",
                        help="Github token that have commit status set permission.",
                        required=True,
                        action="store")

    args = parser.parse_args(args)
    return args

def get_target_pr_list_from_manifest(manifest):
    pr_list = []
    for repo in manifest.repositories:
        if "under-test" in repo and repo["under-test"] is True:
            # commit-id is like "origin/pr/1/merge"
            pull_id = repo["commit-id"].split("/")[2]
            repo = "/".join(repo["repository"][:-4].split("/")[3:])
            pr_list.append((repo, pull_id))
    return pr_list

def set_commit_status(repo, pull_id, status, description, build_url = None):
    pr = gh.get_repo(repo).get_pull(long(pull_id))
    commit = pr.get_commits().reversed[0]
    if build_url:
        commit.create_status(state=status, \
                            description=description, \
                            context='Jenkins', \
                            target_url=build_url)
    else:
        commit.create_status(state=status, \
                            description=description, \
                            context='Jenkins')
    print "Set commit status for {0} pull {1} successfully".format(repo, pull_id)

def set_commit_status_bat(pr_list, status, build_url = None):
    gmt = time.gmtime()
    gmtStr = time.strftime("%b %d, %Y, %I:%M:%S %p ", gmt) + 'GMT'
    description = "Build finished. " + gmtStr

    if len(pr_list) > 1:
        description = description + "[interdependent]"
    for pr in pr_list:
        repo, pull_id = pr
        print "Begin to set commit status"
        set_commit_status(repo, pull_id, status, description, build_url)

def main():
    parsed_args = parse_args(sys.argv[1:])
    global gh
    gh = Github(parsed_args.ghtoken)
    manifest = Manifest(parsed_args.manifest)
    target_pr_list = get_target_pr_list_from_manifest(manifest)
    build_url = parsed_args.build_url
    if build_url:
        if not parsed_args.public_jenkins_url:
            print "public_jenkins_url is required if build-url not None."
            sys.exit(1)
        build_url = urlparse(build_url)._replace(netloc=urlparse(parsed_args.public_jenkins_url).netloc).geturl()
    set_commit_status_bat(target_pr_list, parsed_args.status, build_url)

if __name__ == "__main__":
    main()
