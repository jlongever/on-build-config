#!/usr/bin/env python

"""
pr_parser.py: SCRIPTS that analyse pr information and write parsed pr information
(especially the multi-relate-pr) to post-build proprerties for downstream job.
"""


import argparse
import sys
import os
import github

from github import Github

class PrParser(object):

    def __init__(self):
        """
        __repo - RackHD/on-xxxx, The repo name of which repo triggers the build 
        __target_branch - master etc., The target branch associated with pr
        __merge_commit_sha - origin/pr/1/merge, The merge_commit_sha associated with the pr
        __pull_id - number in string, the pull id associated with the pr
        __actual_commit - sha1 code, the actual commit code associated with the pr
        """
        self.__repo = None
        self.__target_branch = None
        self.__merge_commit_sha = None
        self.__pull_id = None
        self.__actual_commit = None

    def parse_args(self, args):
        """
        Take in values from the user.
        Repo, branch, merge_commit_sha and pull_id are required. This exits if they are not given.
        :return: Parsed args for assignment
        """
        parser = argparse.ArgumentParser()
        parser.add_argument("--repo",
                            help="Git repo of the triggered pr",
                            action="store")
        parser.add_argument("--target_branch",
                            help="The target branch of the pr for the named repo",
                            action="store")
        parser.add_argument("--actual_commit",
                            help="The actual commit of the pr for the named repo",
                            action="store")
        parser.add_argument("--merge_commit_sha",
                            help="The merge_commit_sha of target the pr",
                            action="store")
        parser.add_argument("--pull_id",
                            help="The pull id of target the pr",
                            action="store")
        parsed_args = parser.parse_args(args)
        return parsed_args

    def assign_args(self, args):
        """
        Assign args to member variables.
        :param args: Parsed args from the user
        :return:
        """
        if args.repo:
            self.__repo = args.repo.lower()
        else:
            print "\nMust specify repository url\n"
            sys.exit(1)
        
        if args.target_branch:
            self.__target_branch = args.target_branch
        else:
            print "\nMust specify a branch name\n"
            sys.exit(1)
        
        if args.actual_commit:
            self.__actual_commit = args.actual_commit
        else:
            print "\nMust specify an actual_commit\n"
            sys.exit(1)

        if args.merge_commit_sha:
            self.__merge_commit_sha = args.merge_commit_sha
        else:
            print "\nMust specify a commit-id\n"
            sys.exit(1)

        if args.pull_id:
            self.__pull_id = args.pull_id
        else:
            print "\nMust specify a pull-id\n"
            sys.exit(1)
        
        
    def parse_pr(self, base_repo, base_pull_id):
        """
        get related prs according to the base pr
        :param repo: string, repo name associated with the pr to be parsed
        :param pull_id: number in string, pull request id of the pr to be parsed
        :return related_prs: list of tuple of string: [(repo, sha, pull_id, commit),...] 
        pr list which is the associated with base pr
        """

        #init github  and get related pr object
        HOME = os.environ['HOME']
        with open('{0}/.ghtoken'.format(HOME), 'r') as file:
            TOKEN = file.read().strip('\n')
        gh = Github(TOKEN)
        pr = gh.get_repo(base_repo).get_pull(long(base_pull_id))
        
        #get all comments and description in the pr
        pr_texts = []
        pr_texts.append(pr.body)
        for pr_comment in pr.get_issue_comments():
            pr_texts.append(pr_comment.body)
        
        # pre processing
        pr_text_segment = []
        for pr_text in pr_texts:
            pr_text = pr_text.lower()
            partition = pr_text.split('jenkins')
            if len(partition) <= 1:
                continue
            for segment in partition[1:]:
                pr_text_segment.append("jenkins"+segment)

        #parse pr
        related_prs = []
        for pr_text in pr_text_segment:
            pr_words = pr_text.replace(':', '').replace(',', ' ').split()

            #find keyword "jenkins"
            if 'jenkins' not in pr_words:
                continue
            position = pr_words.index('jenkins')

            #Checks to make sure jenkins is not the last element in pr_words
            if ((position+1) == len(pr_words)) :
                continue

            #analyse dependency relationship, "depend" or "ignore" 
            if ('ignore' not in pr_words[position+1]) and ('depend' not in pr_words[position+1]):
                continue
            
            #find "ignore"
            if 'ignore' in pr_words[position+1]:
                related_prs = None
                print "INFO: \"Jenkins: ignore\" in repo: {0} pull_id: {1}".format(base_repo, base_pull_id)
                break

            #find "depend"
            disp = 2
            if pr_words[position+2] == "on":
                disp += 1 
            for i in range(position+disp, len(pr_words)):
                if 'https//github.com' not in pr_words[i]:
                    break
                dep_pr_url = pr_words[i]
                try:
                    repo = dep_pr_url[:dep_pr_url.rfind('/pull/')].replace('https//github.com/','')
                    assert len(repo.split('/')) == 2
                    pull_id = dep_pr_url[dep_pr_url.rfind('/pull/')+6:]
                    assert pull_id.isalnum() 
                except AssertionError as error:
                    print "ERROR: the pr url {0} is invalid.\n{1}".format(dep_pr_url, error)
                    sys.exit(1)
                try:
                    dep_pr = gh.get_repo(repo).get_pull(long(pull_id))
                    if not dep_pr.mergeable:
                        print "ERROR: the pr of {0} is unmergeable.\n{1}".format(dep_pr_url, pr.mergeable_state)
                        sys.exit(1)
                    sha = 'origin/pr/{0}/merge'.format(pull_id)
                    actual_commit = gh.get_repo(repo).get_pull(long(pull_id)).get_commits().reversed[0].sha
                except Exception as error:
                    print "ERROR: the pr of {0} doesn't exist.\n{1}".format(dep_pr_url, error)
                print "INFO: find one dependency pr, ({0}, {1}, {2}, {3})".format(repo, sha, pull_id, actual_commit)
                related_prs.append((repo, sha, pull_id, actual_commit))
        
        print "INFO: repo: {0}, pull_id: {1} parsing done, recursive parse may continue".format(base_repo, base_pull_id)
        return related_prs


    def get_all_related_prs(self, repo, sha, pull_id, actual_commit):
        """
        RECURSIVELY get ALL related prs information according to the base pr
        :param repo: string, repo name associated with the pr to be parsed
        :param sha: string, the merge_commit_sha associated with the pr to be parsed
        :param pull_id: number in string, pull request id of the pr to be parsed
        :param actual_commit: sha1 code, the actual commit code associated with the pr
        :return all_prs: list of tuple of string: [(repo, sha, pull_id, actual_commit),...] 
        which is the associated with base pr
        """

        #add base pr first
        all_prs = []
        base_pr = [(repo, sha, pull_id, actual_commit)]
        all_prs.extend(base_pr)

        #recursively find dependent pr
        while base_pr:
            _tmp_pr=[]
            for item in base_pr:
                repo, _, pull_id, _ = item
                dependent_prs = self.parse_pr(repo, pull_id)

                #find 'Jenkins: ignore'
                if dependent_prs == None:
                    #find 'Jenkins: ignore' in root trigger pr
                    if len(all_prs) == 1:
                        all_prs = []
                    else:
                        continue
                else:
                    _tmp_pr.extend(dependent_prs)

            #avoid endless loop
            if _tmp_pr:
                _tmp_pr = [t for t in _tmp_pr if t not in all_prs]
            all_prs.extend(_tmp_pr)    
            base_pr = _tmp_pr

        return all_prs
    
    def generate_build_properties(self, all_prs, target_branch):
        """
        generate the content of the build properties file
        :param all_prs: list of tuple of string: [(repo, sha, pull_id, actual_commit),...]
        :param target_branch: string, The target branch associated with pr
        :return properties: string, the contents of build properties file
        """
        properties = ""

        if not all_prs:
            return properties

        is_multi = bool(len(all_prs)>1)
        properties_dic = {}

        #not multi, just trigger the non on-multi job
        if is_multi:
            properties_dic['REPO_NAME'] = ""
            #generate all contents first without distinguish prs
            for pr in all_prs:
                repo, sha, pull_id, actual_commit = pr
                repo_name = repo.split('/')[1]
                if repo_name not in properties_dic['REPO_NAME']:
                    properties_dic['REPO_NAME'] += "{0} ".format(repo_name)
                repo_name = repo.split('/')[1].replace('-','_').upper()
                properties_dic[repo_name] = "true"
                properties_dic["{0}_ghprbGhRepository".format(repo_name)] = repo
                properties_dic["{0}_sha1".format(repo_name)] = sha
                properties_dic["{0}_ghprbActualCommit".format(repo_name)] = actual_commit
                properties_dic["{0}_ghprbPullId".format(repo_name)] = pull_id

            #if on-tasks exists, on-http and on-taskgraph unit-test 
            #will be done in on-tasks sub job so disable them here  
            if properties_dic.has_key('ON_TASKS'):
                for repo_name in ['ON_HTTP', 'ON_TASKGRAPH']:
                    if properties_dic.has_key(repo_name):
                        properties_dic[repo_name] = "false"
            
            #if on-core exists,all unit-test will be done in on-core sub job so disable them here 
            if properties_dic.has_key('ON_CORE'):
                for repo_name in ['ON_HTTP', 'ON_DHCP_PROXY', 'ON_TASKGRAPH', 'ON_TASKS', 'ON_TFTP', 'ON_SYSLOG']:
                    if properties_dic.has_key(repo_name):
                        properties_dic[repo_name] = "false"

                    #if on-core and on-tasks coexist, because the on-http and on-taskgraph depend both the two repos
                    #so in their unit-test both the two commits should be provided, so extra information of on-tasks 
                    #will be passed to on-core 
                    if properties_dic.has_key('ON_TASKS'):
                        properties_dic['ADD_FORKURL'] = 'https://github.com/changev/on-tasks.git'
                        properties_dic['ADD_COMMIT'] = '{0}'.format(properties_dic["ON_TASKS_ghprbActualCommit"])

        for k,v in properties_dic.iteritems():
            properties += "{0}={1}\n".format(k, v)
        
        print "INFO: properties generation done"
        return properties


    def write_build_properties_file(self):
        """
        write build properties file, this likes a main function
        """
        all_prs = self.get_all_related_prs(self.__repo, self.__merge_commit_sha, self.__pull_id, self.__actual_commit)
        properties = self.generate_build_properties(all_prs, self.__target_branch)

        #Jenkins:ingore in root pr -> get_all_related_prs return [] -> no trigger downstream and set commit status "pending"
        if not all_prs:
            file_name = "ignore"
        else:
            repo_name = self.__repo.split('/')[1]
            is_multi = bool(len(all_prs)>1)
            #IMPORTANT! In Jenkins the existence of on-xxx file is the trigger of downstream jobs
            file_name = "on-multi" if is_multi else repo_name

        try:
            with open(file_name, 'w') as target_file:
                target_file.write(properties)
        except IOError as error:
            print "ERROR: file {0} does not exist.\n{1}".format(file_name, error)
            sys.exit(1)
        print "INFO: build properties file **{0}** has been created".format(file_name)
        return
        

def main():
    pr_parser = PrParser()
    passed_args = pr_parser.parse_args(sys.argv[1:])
    pr_parser.assign_args(passed_args)
    pr_parser.write_build_properties_file()

if __name__ == "__main__":
    main()
    sys.exit(0)
