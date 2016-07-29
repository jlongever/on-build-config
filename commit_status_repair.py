#!/usr/bin/env python

import sys
import argparse
from github import Github

def parse_args(args):
        parser = argparse.ArgumentParser()
        parser.add_argument("--repo",
                            action="store")
        parser.add_argument("--pull_id",
                            action="store")
        parser.add_argument("--home",
                            action="store")
        args = parser.parse_args(args)
        return args

args = parse_args(sys.argv[1:])
repo = args.repo
pull_id = args.pull_id

with open('{0}/.ghtoken'.format(args.home), 'r') as f:
    TOKEN = f.read().strip('\n')
gh = Github(TOKEN)
pr = gh.get_repo(repo).get_pull(long(pull_id))

#reversed for inverted order by time
commits_list = pr.get_commits().reversed

the_last_x = 0
test_jenkins_result = {}
prod_jenkins_result= {}
#find lastest
for commit in commits_list:
    commit_status_list = commit.get_statuses()
    for commit_status in commit_status_list:
        print "INFO:{0}, {1}, {2}".format(commit_status.state, commit_status.description, commit_status.created_at)
        if commit_status.description == "Build finished. ":
            the_last_x += 1
            print "INFO: +1s"

            if the_last_x == 1:
                test_jenkins_result = commit_status

            if the_last_x == 2:
                prod_jenkins_result = commit_status
                commit.create_status(commit_status.state, \
                        description=commit_status.description, \
                        context='Jenkins')
                break

#write record file
with file('{0}/record'.format(args.home), 'a') as f:
    f.write('{0},{1},{2}#{3},{4},{5}'.format(test_jenkins_result.state,\
                                            test_jenkins_result.created_at,\
                                            test_jenkins_result.updated_at,\
                                            prod_jenkins_result.state,\
                                            prod_jenkins_result.created_at,\
                                            prod_jenkins_result.updated_at))