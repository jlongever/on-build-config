#!/usr/bin/env python

import sys
import argparse
from github import Github

def parse_args(args):
        parser = argparse.ArgumentParser()
        parser.add_argument("--repo_list",
                            action="store")
        parser.add_argument("--pull_id_list",
                            action="store")
        parser.add_argument("--repo",
                            action="store")
        parser.add_argument("--pull_id",
                            action="store")
        parser.add_argument("--jenkins_url",
                            action="store")
        parser.add_argument("--status",
                            action="store")
        parser.add_argument("--description",
                            action="store")
        parser.add_argument("--home",
                            action="store")
        args = parser.parse_args(args)
        return args

args = parse_args(sys.argv[1:])
repo_list=[]
pull_id_list=[]
if args.pull_id_list != "none":
    tmp_repo_list = args.repo_list.split(',')
    for n, pull_id in enumerate(args.pull_id_list.split(',')):
        if pull_id.isalnum():
            repo_list.append(tmp_repo_list[n])
            pull_id_list.append(long(pull_id))
    args.description += "[dependency]"
elif args.repo != "none":
    repo = args.repo
    repo_list.append(repo)
    pull_id_list.append(long(args.pull_id))

with open('{0}/.ghtoken'.format(args.home), 'r') as file:
    TOKEN = file.read().strip('\n')
gh = Github(TOKEN)

for n, repo in enumerate(repo_list): 
    pr = gh.get_repo(repo).get_pull(long(pull_id_list[n]))
    COMMIT = pr.get_commits().reversed[0]
    COMMIT.create_status(args.status, \
                        description=args.description.replace(',',' '), \
                        context='Jenkins-Dependency-PR')

