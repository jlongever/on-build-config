# Copyright 2016, EMC, Inc.

"""
Module to generate a manifest file
"""
import os
import sys
import json
import shutil

try:
    from RepositoryOperator import RepoOperator
    from manifest import Manifest
    import common
    import config

except ImportError as import_err:
    print import_err
    sys.exit(1)

class ManifestGenerator(object):
    def __init__(self, dest, branch, builddir, git_credential=None, force=False, jobs=1):
        """
        Generate a new manifest according to the manifest sample: manifest.json

        _dest_manifest_file: the path of new manifest
        _branch: the branch name
        _force: overwrite the destination if it exists.
        _builddir: the destination for checked out repositories.
        _jobs: number of parallel jobs to run. The number is related to the compute architecture, multi-core processors...
        :return: None
        """
        self._dest_manifest_file = dest
        self._branch = branch
        self._builddir = builddir
        self._force = force
        self._jobs = jobs
        self._manifest = Manifest.instance_of_sample()
        self.repo_operator = RepoOperator(git_credential)
        self.check_builddir()

    def directory_for_repo(self, repo):
        """
        Get the directory of a repository
        :param repo: a dictionary
        :return: the directary of repository
        """
        if 'checked-out-directory-name' in repo:
            repo_directory = repo['checked-out-directory-name']
        else:
            if 'repository' in repo:
                repo_url = repo['repository']
                repo_directory = common.strip_suffix(os.path.basename(repo_url), ".git")
            else:
                raise ValueError("no way to find basename")

        repo_directory = os.path.join(self._builddir, repo_directory)
        return repo_directory

    def check_builddir(self):
        """
        Checks the given builddir name and force flag.
        Deletes existing directory if one already exists and --force is set
        :return: None
        """
        if os.path.exists(self._builddir):
            if self._force:
                shutil.rmtree(self._builddir)
                print "Removing existing data at {0}".format(self._builddir)
            else:
                print "Unwilling to overwrite destination builddir of {0}".format(self._builddir)
                sys.exit(1)

        os.makedirs(self._builddir)

    def update_repositories_commit(self, repositories):
        """
        update the commit-id of repository with the latest commit id
        :param repositories: a list of repository directory
        :return: None
        """
        for repo in repositories:
            repo_dir = self.directory_for_repo(repo)
            repo["commit-id"] = self.repo_operator.get_latest_commit_id(repo_dir)

    def update_manifest(self):
        """
        update the manifest with branch name
        :return: None
        """
        repositories = self._manifest.repositories
        downstream_jobs = self._manifest.downstream_jobs
        for repo in repositories:
            repo["branch"] = self._branch
            repo["commit-id"] = ""
        self.repo_operator.clone_repo_list(repositories, self._builddir, jobs=self._jobs)
        self.update_repositories_commit(repositories)

        for job in downstream_jobs:
            job["branch"] = self._branch
            repo["commit-id"] = ""
        self.repo_operator.clone_repo_list(downstream_jobs, self._builddir, jobs=self._jobs)
        self.update_repositories_commit(downstream_jobs)

        self._manifest.validate_manifest()

    def generate_manifest(self):
        """
        generate a new manifest
        :return: None
        """
        if os.path.isfile(self._dest_manifest_file):
            if self._force == False:
                raise RuntimeError("The file {0} already exist . \n \
                                    If you want to overrite the file, please specify --force."
                                    .format(dest_file))

        with open(self._dest_manifest_file, 'w') as fp:
            json.dump(self._manifest.manifest, fp, indent=4, sort_keys=True)

class SpecifyDayManifestGenerator(ManifestGenerator):
    def __init__(self, dest, branch, date, builddir, git_credential=None, force=False, jobs=1):
        self._date = date
        self._jenkins_author = config.gitbit_identity["username"]
        super(SpecifyDayManifestGenerator, self).__init__(dest, branch, builddir, git_credential=git_credential, force=force, jobs=jobs)

    def update_repositories_commit(self, repositories):
        for repo in repositories:
            repo_dir = self.directory_for_repo(repo)
            merge_commit = None
            jenkins_commit = None
            try:
                # Get the last merge commit before the date
                merge_commit = self.repo_operator.get_latest_merge_commit_before_date(repo_dir,self._date)
                # Get the last commit of Jenkins before the date
                jenkins_commit = self.repo_operator.get_latest_author_commit_before_date(repo_dir,self._date, self._jenkins_author)
            except Exception,e:
                if merge_commit is None:
                    raise RuntimeError("Failed to update repositories commit: repository {0} \nDue to {1}".format(repo_dir, e))

            repo["commit-id"] = merge_commit
            if len(jenkins_commit) > 0:
                newer_commit = self.repo_operator.get_newer_commit(repo_dir, jenkins_commit, merge_commit)
                repo["commit-id"] = newer_commit

class ExistDirManifestGenerator(ManifestGenerator):
    def __init__(self, dest, builddir, git_credential=None, force=False, jobs=1):
        self._jenkins_author = config.gitbit_identity["username"]
        self._dest_manifest_file = dest
        self._builddir = builddir
        self._force = force
        self._jobs = jobs
        self._manifest = Manifest.instance_of_sample()
        self.repo_operator = RepoOperator(git_credential)
        self.check_builddir()

    def check_builddir(self):
        """
        Checks the given builddir name and force flag.
        Deletes exists directory if one already exists and --force is set
        :return: None
        """
        if not os.path.exists(self._builddir):
            print "The {0} doesn't exist".format(self._builddir)
            sys.exit(1)

    def update_manifest(self):
        """
        update the manifest with branch name
        :return: None
        """
        repositories = self._manifest.repositories
        downstream_jobs = self._manifest.downstream_jobs
        self.update_repositories_commit(repositories)
        self.update_repositories_branch(repositories)
        self.update_repositories_commit(downstream_jobs)
        self.update_repositories_branch(downstream_jobs)
        self._manifest.validate_manifest()

    def update_repositories_branch(self, repositories):
        """
        update the commit-id of repository with the latest commit id
        :param repositories: a list of repository directory
        :return: None
        """
        for repo in repositories:
            repo_dir = self.directory_for_repo(repo)
            repo["branch"] = self.repo_operator.get_current_branch(repo_dir)
