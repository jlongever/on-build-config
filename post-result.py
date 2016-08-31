import json
import requests
import os
import subprocess
import sys

'''
Usage:
python post-result.py \
https://api.github.com/repos/PengTian0/on-core/issues/${PullRequestId}/comments \
http://rackhdci.lss.emc.com \
http://rackhdci.lss.emc.com/job/on-core/851/ \
'#851'
'''

with open('${HOME}/.ghtoken', 'r') as file:
    TOKEN = file.read().strip('\n')

HEADERS = {'Authorization': 'token %s' % TOKEN}

GITHUB_PR_URL = sys.argv[1]
JENKINS_URL = sys.argv[2]
BUILD_URL = sys.argv[3]
BUILD_NAME = sys.argv[4]
FAIL_REPORTS = []

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
    failure_report = "\n"
    failure_report += "BUILD " + build_name + "  Error Logs:\n\n"
    if data:
        failCount = int(data.get('failCount'))
        if failCount > 0:
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
        return failure_report
    else:
        return None

def get_sub_builds(build_url, depth):
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
                for x in range(depth):
                    output += "   "
                output += "- ** BUILD " + sub_build_name + ": " + sub_build_result + "\n"

                sub_outputs = get_sub_builds(sub_build_url, depth+1)
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
                        for x in range(depth):
                            output += "   "
                        output += "- ** BUILD " + sub_build_name + ": " + sub_build_result + "\n"
                        sub_outputs = get_sub_builds(sub_build_url, depth+1)
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
    OUTPUT = '```\n'
    job_name = BUILD_URL.split('/')[-3]
    build_number = BUILD_URL.split('/')[-2]
    
    try:
        build_data = get_build_data(BUILD_URL)
        if build_data:
            build_name = build_data['fullDisplayName']
            build_result = build_data['result']
            OUTPUT +=  "BUILD " + build_name + " : " + build_result + "\n"

            sub_build_outputs = get_sub_builds(BUILD_URL, 1)
            for sub_output in sub_build_outputs:
                OUTPUT += sub_output

            if build_result != "SUCCESS":
                failure_report = generate_failure_report(BUILD_URL, build_name)
                FAIL_REPORTS.append(failure_report)

            if len(FAIL_REPORTS) > 0:
                for fail_report in FAIL_REPORTS:
                    OUTPUT += fail_report
        else:
            build_name = job_name + " #" + build_number   
            failure_report = generate_failure_report(BUILD_URL, build_name)
            FAIL_REPORTS.append(failure_report)

            if len(FAIL_REPORTS) > 0:
                for fail_report in FAIL_REPORTS:
                    OUTPUT += fail_report
            else:
                OUTPUT += "*** BUILD " + build_name + " ***\n"
    except Exception as e:
        print e
        sys.exit(1)
    finally:
        if OUTPUT == "```\n":
            build_name = job_name + " #" + build_number
            OUTPUT += "*** BUILD " + build_name + " ***\n"
        OUTPUT += "```\n"
        post_comments_to_github(OUTPUT, GITHUB_PR_URL, HEADERS)

if __name__ == "__main__":
    main()
