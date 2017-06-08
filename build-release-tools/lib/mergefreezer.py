from github import Github

class MergeFreezer(object):
    """
    Freeze or unfreeze all current open prs of repos_list
    Freeze means a "success" or "failure" commit status will be add to PR
    parameters freeze_* is for customing this commit status
    """
    def __init__(self, ghtoken, repo_list, freeze_context, freeze_desc, unfreeze_desc):
        self.__ghtoken = ghtoken
        self.__repo_list = repo_list
        self.__gh = Github(ghtoken)
        self.__freeze_context = freeze_context
        self.__freeze_desc = freeze_desc
        self.__unfreeze_desc = unfreeze_desc

    def get_repo_open_prs(self, repo):
        return self.__gh.get_repo(repo).get_pulls(state="open")

    def freeze_pr(self, pr):
        try:
            commit = pr.get_commits().reversed[0]
            print "Freezing PR: {0}".format(pr.title)
            commit.create_status(state="failure", \
                                description=self.__freeze_desc, \
                                context=self.__freeze_context)
        except Exception as e:
            raise Exception("Failed to set commit status of for {0}. \n{1}".format(pr.title, e))

    def freeze_prs(self, pr_list):
        try:
            for pr in pr_list:
                # When freezing, a frozen PR won't be changed
                if not self.is_frozen(pr):
                    self.freeze_pr(pr)
        except Exception as e:
            raise Exception("Failed to freeze prs. \n{0}".format(e))

    def freeze_all_prs(self):
        # PyGithub get_pulls method return github.PaginatedList.PaginatedList
        # This list type doesn't support list combining.
        for repo in self.__repo_list:
            repo_open_prs = self.get_repo_open_prs(repo)
            self.freeze_prs(repo_open_prs)

    def unfreeze_pr(self, pr):
        try:
            commit = pr.get_commits().reversed[0]
            print "Unfreezing PR: {0}".format(pr.title)
            commit.create_status(state="success", \
                        description=self.__unfreeze_desc, \
                        context=self.__freeze_context)
        except Exception as e:
            raise Exception("Failed to set commit status for pr {0}. \n{1}".format(pr.title, e))

    def unfreeze_prs(self, pr_list):
        try:
            # Github api is actually accessed in the loop.
            for pr in pr_list:
                # When unfreezing, a unfrozen PR won't be changed
                if self.is_frozen(pr):
                    self.unfreeze_pr(pr)
        except Exception as e:
            raise Exception("Failed to unfreeze prs. \n{0}".format(e))

    def unfreeze_all_prs(self):
        for repo in self.__repo_list:
            repo_open_prs = self.get_repo_open_prs(repo)
            self.unfreeze_prs(repo_open_prs)

    def is_frozen(self, pr):
        try:
            commit = pr.get_commits().reversed[0]
            statuses = commit.get_statuses()
            for status in statuses:
                if status.context == self.__freeze_context:
                    if status.state == "failure":
                        return True
                    elif status.state == "success":
                        return False
                    else:
                        print "Commit status in wrong format!"
                        raise Exception("There's illegal frozen commit status of PR:\n{0}".format(pr.title))
                else:
                    continue
            return False
        except Exception as e:
            raise Exception("Failed to get commit status of pr {0}. \n{1}".format(pr.title, e))
