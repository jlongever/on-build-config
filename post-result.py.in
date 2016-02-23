import json
import requests
import os
import subprocess
import sys

with open('${HOME}/.ghtoken', 'r') as file:
    TOKEN = file.read().strip('\n')

HEADERS = {'Authorization': 'token %s' % TOKEN}
GITHUB_PR_URL = sys.argv[1]
JENKINS_URL = sys.argv[2]
BUILD_NAME = sys.argv[3]

r = requests.get(JENKINS_URL)
if r.status_code == 200:
    OUTPUT = '```\n'
    OUTPUT += "*** BUILD " + BUILD_NAME + " ***\n"
    data = r.json()
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
                    OUTPUT += name + details + stack + "\n"
    OUTPUT += "```\n"
    body = { "body" : OUTPUT }
    r = requests.post(GITHUB_PR_URL,headers=HEADERS,data=json.dumps(body))
    print r.status_code
