#!/usr/bin/env python

###############################
# parse a manifest file to get the commit for each repo.
# parse commitstring.txt in docker image for each repo image.
# Check consistency of two commit hash.
###############################

import json
import sys
import os
import argparse
import common
from manifest import Manifest

def parse_args(args):
    """
    Parse script arguments.
    :return: Parsed args for assignment
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest-file',
                        required=True,
                        help="The file path of manifest",
                        action='store')

    parser.add_argument('--parameters-file',
                        help="The repo commit id infomation in docker images",
                        required=True,
                        action='store')

    parsed_args = parser.parse_args(args)
    return parsed_args

def get_repo_commit(manifest_file):
    """
    build {repository:commit-id} dictionary, return the dict.
    """
    manifest = Manifest(manifest_file)
    manifest.validate_manifest()
    repo_commit_dict = {}
    for repo in manifest.repositories:
        repo_name = common.strip_suffix(os.path.basename(repo["repository"]), ".git")
        commit_id = repo["commit-id"]
        repo_commit_dict[repo_name] = commit_id
    print "[DEBUG] manifest repo_commit dict:", repo_commit_dict
    return repo_commit_dict

def check_commit_version(repo_commit_dict, docker_repo_commit_file):
    """
    check the commit hashcode between manifest and docker build.
    """
    version_correct = True
    f = open(docker_repo_commit_file)
    for line in f:
        print "[DEBUG] get docker repo commit info:(%s)" %line
        line_list = line.strip().split(':')
        hashcode = repo_commit_dict.get(line_list[0])
        if not hashcode.startswith(line_list[1]) :
            print "[ERROR] mismatch: repo:%s, manifest commit:%s, docker build commit:%s" % (line_list[0], hashcode, line_list[1])
            version_correct = False
    f.close()   
    return version_correct



def main():
    args = parse_args(sys.argv[1:])
    print "[DEBUG] args manifest_file:%s, docker_repo_commit_file:%s" % (args.manifest_file, args.parameters_file)
    repo_commit_dict = get_repo_commit(args.manifest_file)
    version_correct = check_commit_version(repo_commit_dict, args.parameters_file)
    print "[INFO] docker commit version check for each repo is correct:", version_correct
    if not version_correct :
        print "[ERROR] mismatch: docker commit version and manifest "
        sys.exit(1)

if __name__ == '__main__':
    main()

