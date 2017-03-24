#!/usr/bin/env python

import json
import requests
import os
import subprocess
import sys
import argparse
from manifest import Manifest
import common

'''
Usage:
python post-result.py \
--manifest_file manifest \
--jenkins_url http://rackhdci.lss.emc.com \
--build_url http://rackhdci.lss.emc.com/job/on-core/851/ \
--public_jenkins_url http://147.178.202.18/
'''

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest_file',
                        required=True,
                        help="The manifest file path",
                        action="store")
    parser.add_argument('--jenkins_url',
                        required=True,
                        help="The url of the internal jenkins",
                        action="store")
    parser.add_argument('--build_url',
                        required=True,
                        help="the url of the build in jenkins",
                        action="store")
    parser.add_argument('--public_jenkins_url',
                        required=True,
                        help="the url of the public jenkins",
                        action="store")
    parser.add_argument('--ghtoken',
                        required=True,
                        help="the token of the github",
                        action="store")

    parsed_args = parser.parse_args(args)
    return parsed_args

def get_build_data(build_url):
    '''
    get the json data of a build
    :param build_url: the url of a build in jenkins
    :return: json data of the build if succeed to get the json data
             None if failed to get the json data
    '''
    r = requests.get(build_url + "/api/json?depth=2")
    if is_error_response(r):
        print "Failed to get api json of {0}".format(build_url)
        print r.text
        print r.status_code
        return None
    else:
        data = r.json()
        return data

def get_test_report(build_url):
    '''
    get the test report of a build
    :param build_url: the url of a build in jenkins
    :return: json data of test report of the build if succeed to get the json data
             None if failed to get the json data
    '''
    r = requests.get(build_url + "/testReport/api/json")
    if is_error_response(r):
        print "Failed to get testReport of {0}".format(build_url)
        print r.text
        print r.status_code
        return None
    else:
        data = r.json()
        return data     

def generate_failure_report(build_url, build_name):
    '''
    get the test report and generate a report which contains the error log
    :param build_url: the url of a build in jenkins
    :param build_name: build name consist of job name and build number
    :return: failure report if succeed to get the json data of test report 
             None if failed to get the json data of test report
    '''
    data = get_test_report(build_url)
    if data:
        failCount = int(data.get('failCount'))
        if failCount > 0:
            failure_report = "\n<details>\n"
            failure_report += "<summary>BUILD " + build_name + "  Error Logs  &#9660;</summary>"
            for suite in data['suites']:
                for case in suite['cases']:
                    if case['errorDetails']:
                        name = case['name']
                        errorDetails = case['errorDetails']
                        errorStackTrace = case['errorStackTrace']
                        name = "Test Name: " + name + "\n"
                        details = "Error Details: " + errorDetails + "\n"
                        stack = "Stack Trace: " + errorStackTrace + "\n"
                        failure_report += name + details + stack + "\n"
            failure_report += "</details>\n"
            return failure_report
    
    return None

def get_sub_builds(build_url, fail_reports, depth = 1):
    '''
    get sub builds of a build
    :param build_url: the url of a build in jenkins
    :param depth: the depth of the nested sub build
    :return: a list of string which contains the result , build number of the sub builds
    '''
    build_data = get_build_data(build_url)
    outputs = []
    if build_data:
        if 'subBuilds' in build_data:
            '''
            get sub builds results
            '''
            for subBuild in build_data['subBuilds']:
                output = ""
                sub_build_name = subBuild['jobName'] + "  #" + str(subBuild['buildNumber'])
                sub_build_result = subBuild['result']
                sub_build_url = jenkins_url + "/" + subBuild['url']
                public_sub_build_url = sub_build_url.replace(jenkins_url, public_jenkins_url)
                for x in range(depth):
                    output += "   "
                output += "- ** BUILD [" + sub_build_name + "](" + public_sub_build_url + "): " + sub_build_result + "\n"

                sub_outputs = get_sub_builds(sub_build_url, depth = depth+1)
                if len(sub_outputs) >0 :
                    for sub_output in sub_outputs:
                        output += sub_output
                outputs.append(output)
                if sub_build_result != "SUCCESS":
                    failure_report = generate_failure_report(sub_build_url, sub_build_name)
                    fail_reports.append(failure_report)

        if 'actions' in build_data:
            for action in build_data['actions']:
                if 'triggeredBuilds' in action:
                    '''
                    get triggered builds results
                    '''
                    for subBuild in action['triggeredBuilds']:
                        output = "\n"
                        sub_build_name = subBuild['fullDisplayName']
                        sub_build_result = subBuild['result']
                        sub_build_url = subBuild['url']
                        public_sub_build_url = sub_build_url.replace(jenkins_url, public_jenkins_url)
                        for x in range(depth):
                            output += "   "
                        output += "- ** BUILD [" + sub_build_name + "](" + public_sub_build_url + "): " + sub_build_result + "\n"
                        sub_outputs = get_sub_builds(sub_build_url, depth = depth+1)
                        if len(sub_outputs) > 0:
                            for sub_output in sub_outputs:
                                output += sub_output
                        outputs.append(output)
                        if sub_build_result != "SUCCESS":
                            failure_report = generate_failure_report(sub_build_url, sub_build_name)
                            fail_reports.append(failure_report)
    return outputs

def is_error_response(res):
    """
    check the status code of http response
    :param res: http response
    :return: True if the status code less than 200 or larger than 206;
             False if the status code is between 200 and 206
    """
    if res is None:
        return True
    if res.status_code < 200 or res.status_code > 299:
        return True
    return False

def post_comments_to_github(comments, github_pr_url, headers):
    '''
    post comments to github Pull Request
    :param comments: comments to be posted to Pull Request
    :param github_pr_url: the url of the PR
    :param headers: the request headers which usually contains the "Authorization" field
    :return: exit with error code 1 if get bad response for the request
             return null if get successful response
    '''
    body = { "body" : comments }
    r = requests.post(github_pr_url,headers=headers,data=json.dumps(body))
    if is_error_response(r):
        print "Failed to post comments to pull request {0}".format(github_pr_url)
        print r.text
        print r.status_code
        sys.exit(1)
    else:
        print "Succeed to post comments to pull request {0}".format(github_pr_url)
        return
 

def get_prs(manifest):
    PRs = {}
    for repo in manifest.repositories:
        if "under-test" in repo and repo["under-test"] == True:
            pr_id = repo["commit-id"].split('/')[-2]
            repo_name = common.strip_suffix(os.path.basename(repo["repository"]), ".git")
            repo_owner = repo["repository"].split('/')[-2]
            PRs[repo_name] = {"repo_owner": repo_owner, "pull_request_id": pr_id}
    return PRs
                      
def main():
    # parse arguments
    args = parse_args(sys.argv[1:])
    jenkins_url = args.jenkins_url
    build_url = args.build_url
    public_jenkins_url = args.public_jenkins_url
    token = args.ghtoken

    HEADERS = {'Authorization': 'token %s' % token}

    manifest = Manifest(args.manifest_file)
    pull_requests= get_prs(manifest)

    for repo, pr in pull_requests.iteritems():
        repo_owner = pr["repo_owner"]
        pr_id = pr["pull_request_id"]
        pr_url = "https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pr_id}/comments"\
                 .format(repo_owner=repo_owner, repo_name=repo, pr_id=pr_id)
        print pr_url
        post_results(pr_url, jenkins_url, build_url, public_jenkins_url, HEADERS)


def post_results(pr_url, jenkins_url, build_url, public_jenkins_url, HEADERS):
    OUTPUT = ""
    fail_reports = []
    job_name = build_url.split('/')[-3]
    build_number = build_url.split('/')[-2]
    public_build_url = "{url}/blue/organizations/jenkins/{job_name}/detail/{job_name}/{build_number}/pipeline"\
                       .format(url=public_jenkins_url, job_name=job_name, build_number=build_number)

    try:
        build_data = get_build_data(build_url)
        if build_data:
            build_name = build_data['fullDisplayName']
            build_result = build_data['result']
            OUTPUT +=  "BUILD [" + build_name + "](" + public_build_url + ") : " + build_result + "\n"

            sub_build_outputs = get_sub_builds(build_url, fail_reports)
            for sub_output in sub_build_outputs:
                OUTPUT += sub_output
        else:
            build_name = job_name + " #" + build_number
            OUTPUT += "*** BUILD [" + build_name + "](" + public_build_url + ") ***\n"

        failure_report = generate_failure_report(build_url, build_name)
        fail_reports.append(failure_report)

        if len(fail_reports) > 0:
            for fail_report in fail_reports:
                if fail_report is not None:
                    OUTPUT += fail_report       

    except Exception as e:
        print e
        sys.exit(1)
    finally:
        if OUTPUT == "":
            build_name = job_name + " #" + build_number
            OUTPUT += "*** BUILD [" + build_name + "](" + public_build_url + ") ***\n"

        post_comments_to_github(OUTPUT, pr_url, HEADERS)

if __name__ == "__main__":
    main()
