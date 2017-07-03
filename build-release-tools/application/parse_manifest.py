#!/usr/bin/env python

###############################
# parse a manifest file to get the repositories which is a PR
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
                        help="The jenkins parameter file that will used for succeeding Jenkins job",
                        action='store',
                        default="downstream_parameters")

    parsed_args = parser.parse_args(args)
    return parsed_args

def get_repositories_under_test(manifest_file):
    """
    get repositories whose commit-id is somethint like: origin/pr/111/merge
    """
    manifest = Manifest(manifest_file)
    repos_under_test = []
    for repo in manifest.repositories:
        if "commit-id" in repo:
            if "origin/pr" in repo["commit-id"]:
                repo_name = common.strip_suffix(os.path.basename(repo["repository"]), ".git")
                repos_under_test.append(repo_name)
    return repos_under_test

def write_downstream_parameters(repos_under_test, parameters_file):
    params = {}
    params['REPOS_UNDER_TEST'] = ','.join(repos_under_test)

    repos_need_unit_test = []
    for repo_name in repos_under_test:
        if repo_name in ["on-core", "on-tasks", "on-http", "on-tftp", "on-dhcp-proxy", "on-taskgraph", "on-syslog", "image-service"]:
            repos_need_unit_test.append(repo_name)

        if repo_name == "on-core":
            repos_depends = ["on-tasks", "on-http", "on-tftp", "on-dhcp-proxy", "on-taskgraph", "on-syslog"]
            repos_need_unit_test.extend(repos_depends)

        if repo_name == "on-tasks":
            repos_depends = ["on-http", "on-taskgraph"]
            repos_need_unit_test.extend(repos_depends)

    repos_need_unit_test = list(set(repos_need_unit_test))
    if len(repos_need_unit_test) > 0:
        params['REPOS_NEED_UNIT_TEST'] = ','.join(repos_need_unit_test)
    common.write_parameters(parameters_file, params)

def main():
    args = parse_args(sys.argv[1:])
    repos_under_test = get_repositories_under_test(args.manifest_file)
    write_downstream_parameters(repos_under_test, args.parameters_file)

if __name__ == '__main__':
    main()
