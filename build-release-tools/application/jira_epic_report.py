#!/usr/bin/env python
# Copyright 2017, DELLEMC, Inc.
from jira import JIRA
import sys
import argparse
import common

class JIRAOperator(object):
    def __init__(self, server, username, password):
        # Initial jira 
        # set verify as false to get rid of requests.exceptions.SSLError: [Errno 1] _ssl.c:507: error:14090086:SSL routines:SSL3_GET_SERVER_CERTIFICATE:certificate verify failed
        options = {'server': server, 'verify': False}
        self.__jira = JIRA(options, basic_auth=(username, password))
        
    def search_issues(self, sql_str):
        issues = self.__jira.search_issues(sql_str)
        return issues

    def search_open_bugs_by_priority(self, project, priority, end_status="done"):
        JQL_str="project in ({0}) and issuetype = Bug and status not in ({1}) and priority = {2}".format(project, end_status, priority)
        return self.search_issues(JQL_str)

def parse_command_line(args):
    """
    Parse script arguments.
    :return: Parsed args for assignment
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--jira_server",
                        required=True,
                        help="The server url of jira",
                        action="store")
    parser.add_argument("--username",
                        required=True,
                        help="the username of jira",
                        action="store")
    parser.add_argument("--password",
                        required=True,
                        help="the password of jira",
                        action="store")
    parser.add_argument('--parameters-file',
                        help="The jenkins parameter file that will used for succeeding Jenkins job",
                        action='store',
                        default="downstream_parameters")

    parsed_args = parser.parse_args(args)
    return parsed_args

def main():
    # parse arguments
    args = parse_command_line(sys.argv[1:])
    jira_operator = JIRAOperator(args.jira_server,args.username,args.password)
    report = {}
    p1_bugs = jira_operator.search_open_bugs_by_priority("RACKHD", "P1")
    report["P1_ISSUES_COUNT"] = len(p1_bugs)

    # Create a java properties file to pass down parameters to downstream pipeline steps
    common.write_parameters(args.parameters_file, report)

if __name__ == "__main__":
    main()
    sys.exit(0)
