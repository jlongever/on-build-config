import json
import requests
import os
import subprocess
import sys
import argparse

'''
Usage:
python post-result.py \
--github_pr_url https://api.github.com/repos/RackHD/on-core/issues/${PullRequestId}/comments \
--jenkins_url http://rackhdci.lss.emc.com \
--build_url http://rackhdci.lss.emc.com/job/on-core/851/ \
--build_name '#851' \
--public_jenkins_url http://147.178.202.18/
'''

with open('${HOME}/.ghtoken', 'r') as file:
    TOKEN = file.read().strip('\n')

HEADERS = {'Authorization': 'token %s' % TOKEN}

GITHUB_PR_URL = ""
JENKINS_URL = ""
BUILD_URL = ""
BUILD_NAME = ""
PUBLIC_JENKINS_URL = ""
FAIL_REPORTS = []

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--github_pr_url',
                        required=True,
                        help="The url of the pull request in github",
                        action="store")
    parser.add_argument('--jenkins_url',
                        required=True,
                        help="The url of the internal jenkins",
                        action="store")
    parser.add_argument('--build_url',
                        required=True,
                        help="the url of the build in jenkins",
                        action="store")
    parser.add_argument('--build_name',
                        required=True,
                        help="the name of the build in jenkins",
                        action="store")
    parser.add_argument('--public_jenkins_url',
                        required=True,
                        help="the url of the public jenkins",
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

def get_sub_builds(build_url, depth = 1):
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
                sub_build_url = JENKINS_URL + "/" + subBuild['url']
                public_sub_build_url = sub_build_url.replace(JENKINS_URL, PUBLIC_JENKINS_URL)
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
                    FAIL_REPORTS.append(failure_report)

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
                        public_sub_build_url = sub_build_url.replace(JENKINS_URL, PUBLIC_JENKINS_URL)
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
                            FAIL_REPORTS.append(failure_report)
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
                
def main():
    OUTPUT = ""
    job_name = BUILD_URL.split('/')[-3]
    build_number = BUILD_URL.split('/')[-2]
    public_build_url = BUILD_URL.replace(JENKINS_URL, PUBLIC_JENKINS_URL)
    try:
        build_data = get_build_data(BUILD_URL)
        if build_data:
            build_name = build_data['fullDisplayName']
            build_result = build_data['result']
            OUTPUT +=  "BUILD [" + build_name + "](" + public_build_url + ") : " + build_result + "\n"

            sub_build_outputs = get_sub_builds(BUILD_URL)
            for sub_output in sub_build_outputs:
                OUTPUT += sub_output

        else:
            build_name = job_name + " #" + build_number
            OUTPUT += "*** BUILD [" + build_name + "](" + public_build_url + ") ***\n"

            failure_report = generate_failure_report(BUILD_URL, build_name)
            FAIL_REPORTS.append(failure_report)

        if len(FAIL_REPORTS) > 0:
            for fail_report in FAIL_REPORTS:
                if fail_report is not None:
                    OUTPUT += fail_report       

    except Exception as e:
        print e
        sys.exit(1)
    finally:
        if OUTPUT == "":
            build_name = job_name + " #" + build_number
            OUTPUT += "*** BUILD [" + build_name + "](" + public_build_url + ") ***\n"

        post_comments_to_github(OUTPUT, GITHUB_PR_URL, HEADERS)

if __name__ == "__main__":
    # parse arguments
    parsed_args = parse_args(sys.argv[1:])
    GITHUB_PR_URL = parsed_args.github_pr_url
    JENKINS_URL = parsed_args.jenkins_url
    BUILD_URL = parsed_args.build_url
    BUILD_NAME = parsed_args.build_name
    PUBLIC_JENKINS_URL = parsed_args.public_jenkins_url

    main()
