from github import Github, Requester
import random

class MergeFreezer(object):
    """
    Freeze or unfreeze all current open prs of repos_list
    Freeze means a "success" or "failure" commit status will be add to PR
    parameters freeze_* is for customing this commit status
    """
    def __init__(self, admin_ghtoken, puller_ghtoken_pool ,repo_list, freeze_context, freeze_desc, unfreeze_desc):
        self.__admin_ghtoken = admin_ghtoken
        self.__puller_ghtoken_pool = puller_ghtoken_pool
        self.__puller_ghtoken_pool = puller_ghtoken_pool.split()
        self.__repo_list = repo_list
        self.__freeze_context = freeze_context
        self.__freeze_desc = freeze_desc
        self.__unfreeze_desc = unfreeze_desc
        # a pygithub private class method
        self.__admin_requester = Requester.Requester(self.__admin_ghtoken,None,"https://api.github.com", 10, None, None,'PyGithub/Python',30,False)
    
    @property
    def __gh(self):
        """
        return a Github instance with random token
        """
        ghtoken_pool_size = len(self.__puller_ghtoken_pool)
        random_index = random.randint(0, ghtoken_pool_size-1)
        this_choice = self.__puller_ghtoken_pool[random_index]
        return Github(this_choice)

    def get_repo_open_prs(self, repo):
        return self.__gh.get_repo(repo).get_pulls(state="open")

    def freeze_pr(self, pr):
        try:
            commit = pr.get_commits().reversed[0]
            print "Freezing PR: " + pr.title
            commit._requester = self.__admin_requester
            commit.create_status(state="failure", \
                                description=self.__freeze_desc, \
                                context=self.__freeze_context)
        except Exception as e:
            raise Exception("Failed to set commit status of for " + pr.title + "\n{0}".format(e))

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
            print "Unfreezing PR: " + pr.title
            commit._requester = self.__admin_requester
            commit.create_status(state="success", \
                        description=self.__unfreeze_desc, \
                        context=self.__freeze_context)
        except Exception as e:
            raise Exception("Failed to set commit status for pr " + pr.title +"\n{0}".format(e))

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
                        raise Exception("There's illegal frozen commit status of PR:\n" + pr.title)
                else:
                    continue
            return False
        except Exception as e:
            raise Exception("Failed to get commit status of pr " + pr.title + "\n{0}".format(e))
