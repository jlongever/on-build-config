#!/usr/bin/env python

"""
pr_parser.py: SCRIPTS that analyse pr information and write parsed pr information
(especially the multi-relate-pr) to post-build proprerties for downstream job.
"""


import argparse
import sys
import os
import github
import collections

from github import Github
from manifest import Manifest

class PrParser(object):

    def __init__(self, change_url, target_branch, ghtoken):
        """
        Initialize PrParser with change_url
        """
        assert change_url, "Error: PR URL is None!"
        assert ghtoken, "Error: ghtoken is None!"
        assert target_branch, "Error: target_branch is None!"
        url_segments = change_url.split("/")
        self.__repo = "/".join(change_url.split("/")[-4:-2]).lower()
        self.__target_branch = target_branch
        self.__pull_id = url_segments[-1]
        self.__merge_commit_sha = "origin/pr/{0}/merge".format(self.__pull_id)
        self.__pr_list = [self.__repo]
        self.__pr_connectivity_map = collections.defaultdict(dict)
        self.__gh = Github(ghtoken)
    def parse_pr(self, base_repo, base_pull_id):
        """
        get related prs according to the base pr
        :param repo: string, repo name associated with the pr to be parsed
        :param pull_id: number in string, pull request id of the pr to be parsed
        :return related_prs: list of tuple of string: [(repo, sha, pull_id, commit),...] 
        pr list which is the associated with base pr
        """

        #init github  and get related pr object
        gh = self.__gh
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
            jenkins_index = pr_text.find("jenkins")
            if jenkins_index != -1:
                pr_text = pr_text[jenkins_index:]
                partition = [i for i in pr_text.split('jenkins') if i]
                for segment in partition:
                    pr_text_segment.append("jenkins"+segment)

        #parse pr
        related_prs = []
        for pr_text in pr_text_segment:
            pr_words = pr_text.replace(':', '').replace(',', ' ').split()

            #find keyword "jenkins"
            if 'jenkins' not in pr_words:
                continue
            position = pr_words.index('jenkins')

            #Checks to make sure the pr_words are long enough to parse.
            #Needs to be at least length of 3 ("Jenkins ignore/depend PR")
            if ((position+2) >= len(pr_words)) :
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
                except Exception as error:
                    print "ERROR: the pr of {0} doesn't exist.\n{1}".format(dep_pr_url, error)
                print "INFO: find one dependency pr, ({0}, {1}, {2})".format(repo, sha, pull_id)
                related_prs.append((repo, sha, pull_id))
                self.__pr_connectivity_map[base_repo][repo] = True
                if not self.__pr_connectivity_map[repo].has_key(base_repo):
                    self.__pr_connectivity_map[repo][base_repo] = False
                if repo not in self.__pr_list:
                    self.__pr_list.append(repo)
        
        print "INFO: repo: {0}, pull_id: {1} parsing done, recursive parse may continue".format(base_repo, base_pull_id)
        return related_prs


    def get_all_related_prs(self, repo, sha, pull_id):
        """
        RECURSIVELY get ALL related prs information according to the base pr
        :param repo: string, repo name associated with the pr to be parsed
        :param sha: string, the merge_commit_sha associated with the pr to be parsed
        :param pull_id: number in string, pull request id of the pr to be parsed
        :return all_prs: list of tuple of string: [(repo, sha, pull_id),...] 
        which is the associated with base pr
        """

        #add base pr first
        all_prs = []
        base_pr = [(repo, sha, pull_id)]
        all_prs.extend(base_pr)

        #recursively find dependent pr
        while base_pr:
            _tmp_pr=[]
            for item in base_pr:
                repo, _, pull_id = item
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

    def get_under_test_prs(self):
        """
        According to the self.__pr_connectivity_map and self.__pr_list
        to find those under_test_prs.
        under_test_pr: 
            1. root pr(which trigger this build) is under_test
            2. pr that diconnected with under_test_pr is under_test_pr
        """
        # the final filtered results
        # under_test_prs to be parsed to find related under_test_prs
        tmp_under_test_prs = [self.__pr_list[0]]
        # wich is the under_test_prs after parsing
        under_test_prs = [self.__pr_list[0]]
        # prs haven been parsed, for preventing infinite loop
        parsed_prs = []
        while tmp_under_test_prs:
            parsed_prs.extend(tmp_under_test_prs)
            # the next tmp_under_test_prs
            tmp_tmp_under_test_prs = []
            for under_test_pr in tmp_under_test_prs:
                # must be single pr, depends on None PR
                if not self.__pr_connectivity_map.has_key(under_test_pr):
                    continue
                for pr in self.__pr_list:
                    # disconnected with this pr
                    if not self.__pr_connectivity_map[under_test_pr].has_key(pr):
                        continue
                    # if diconnected , [under_test_pr][pr] and [under_test_pr][pr] both equal True
                    # if one-way connected, one is True the other if False
                    if self.__pr_connectivity_map[under_test_pr][pr] and \
                        self.__pr_connectivity_map[pr][under_test_pr]:
                        # diconnected with under_test_pr means this pr is under test too
                        under_test_prs.append(pr)
                        if pr not in parsed_prs:
                            tmp_tmp_under_test_prs.append(pr)
            tmp_under_test_prs = tmp_tmp_under_test_prs
        return under_test_prs
    
    def get_latest_commit(self, repo, branch):
        """
        Get repo latest commit of the specific branch
        """
        gh = self.__gh
        branch = gh.get_repo(repo).get_branch(branch)
        latest_commit = branch.commit.sha
        return latest_commit

    def wrap_manifest_file(self, file_path):
        """
        Generated manifest file
        """
        all_prs = self.get_all_related_prs(self.__repo, self.__merge_commit_sha, self.__pull_id)
        under_test_prs = self.get_under_test_prs()
        # instance of manifest template
        manifest = Manifest.instance_of_sample("manifest-pr-gate.json")

        # wrap with pr
        repo_url_list = [repo["repository"] for repo in manifest.repositories]
        for pr in all_prs:
            repo, sha1, _ = pr
            repo_url = "https://github.com/{0}.git".format(repo)
            # uniform the repo_url case, make sure the url is completely consistent with repo in the manifest
            repo_url = [url for url in repo_url_list if url.lower()== repo_url][0]
            if repo in under_test_prs:
                manifest.update_manifest(repo_url, "", sha1, True)
            else:
                manifest.update_manifest(repo_url, "", sha1, False)

        # fill in blank commit with latest commit sha
        for repo in manifest.repositories:
            if 'commit-id' in repo and repo['commit-id'] == "":
                repo_name = "/".join(repo["repository"][:-4].split("/")[3:])
                latest_commit = self.get_latest_commit(repo_name, self.__target_branch)
                repo["commit-id"] = latest_commit

        manifest.validate_manifest()
        manifest.dump_to_json_file(file_path)

def parse_args(args):
    """
    Take in values from the user.
    Repo, branch, merge_commit_sha and pull_id are required. This exits if they are not given.
    :return: Parsed args for assignment
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--change-url",
                        help="Url of the triggered pr",
                        action="store")
    parser.add_argument("--target-branch",
                        help="The target branch of the pr for the named repo",
                        required=True,
                        action="store")
    parser.add_argument("--ghtoken",
                        help="Github token that have commit status set permission.",
                        required=True,
                        action="store")
    parser.add_argument("--manifest-file-path",
                        help="The file path of wanted manifest output, relevent or absolute",
                        required=True,
                        action="store")

    parsed_args = parser.parse_args(args)
    return parsed_args

def main():
    parsed_args = parse_args(sys.argv[1:])
    pr_parser = PrParser(parsed_args.change_url, parsed_args.target_branch, parsed_args.ghtoken)
    pr_parser.wrap_manifest_file(parsed_args.manifest_file_path)

if __name__ == "__main__":
    main()
    sys.exit(0)
