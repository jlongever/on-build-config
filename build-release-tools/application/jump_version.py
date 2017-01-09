#!/usr/bin/env python
# Copyright 2015-2016, EMC, Inc.

"""
The script will update the version of debian/changelog and package.json files, inside all git repos under the folder which "build-dir" param specified. 
The version field in debian/changelog file will be updated to given version ( via "dch  -v $ver -b -m" command).
The version field in package.json will be updated to given version (via "npm version --no-git-tag-version #ver" command)

usage:
./on-build-config/build-release-tools/HWIMO-BUILD on-build-config/build-release-tools/application/jump_version.py
--build-dir d/ \
--version 1.2.6 \
--publish \
--git-credential https://github.com,GITHUB \
--message "new branch 1.2.6"

The required parameters: 
build-dir: The top directory which stores all the cloned repositories
version: The new release version

The optional parameters:
message (default value is "new release" + version )
publish: If true, the updated changlog will be push to github.
git-credential: url, credentials pair for the access to github repos.
                For example: https://github.com,GITHUB
                GITHUB is an environment variable: GITHUB=username:password
                If parameter publish is true, the parameter is required.
"""
import os
import sys
import argparse

try:
    from RepositoryOperator import RepoOperator
    from npm import NPM
    import common
except ImportError as import_err:
    print import_err
    sys.exit(1)

class ChangelogUpdater(object):
    def __init__(self, repo_dir, version):
        """
        The module updates debian/changelog under the directory of repository
        _repo_dir: the directory of the repository
        _version: the new version which is going to be updated to changelog
        """
        self._repo_dir = repo_dir
        self._version = version
        self.repo_operator = RepoOperator()
 
    def debian_exist(self):
        """
        check whether debian directory under the repository
        return: True if debian exist
                False
        """
        if os.path.isdir(self._repo_dir):
            for filename in os.listdir(self._repo_dir):
                if filename == "debian":
                    return True
        return False

    def get_repo_name(self):
        """
        get the name of the repository
        :return: the name of the repository
        """
        repo_url = self.repo_operator.get_repo_url(self._repo_dir)
        repo_name = common.strip_suffix(os.path.basename(repo_url), ".git")
        return repo_name

    def update_changelog(self, message=None):
        """
        add an entry to changelog
        :param message: the message which is going to be added to changelog
        return: Ture if changelog is updated
                False, otherwise
        """
        repo_name = self.get_repo_name()
        debian_exist = self.debian_exist()
        linked = False
        if not debian_exist:
            # Handle repository which contains debianstatic/repository_name folder, 
            # for example: debianstatic/on-http
            for filename in os.listdir(self._repo_dir):
                if filename == "debianstatic":
                    debianstatic_dir = os.path.join(self._repo_dir, "debianstatic")
                    for debianstatic_filename in os.listdir(debianstatic_dir):
                        if debianstatic_filename == repo_name:
                            debianstatic_repo_dir = "debianstatic/{0}".format(repo_name)
                            common.link_dir(debianstatic_repo_dir, "debian", self._repo_dir)
                            linked = True

        if not debian_exist and not linked:
            return False

        print "start to update changelog of {0}".format(self._repo_dir)
        # -v: Add a new changelog entry with version number specified
        # -b: Force a version to be less than the current one
        # -m: Don't change (maintain) the trailer line in the changelog entry; i.e.
        #     maintain the maintainer and date/time details
        try:
            cmd_args = ["dch", "-v", self._version, "-b", "-m"]
            if message is None:
                message = "new release {0}".format(self._version)
            cmd_args += ["-p", message]
            common.run_command(cmd_args, directory=self._repo_dir)
      
            if linked:
                os.remove(os.path.join(self._repo_dir, "debian"))

            return True
        except Exception, err:
            raise RuntimeError("Failed to add an entry for {0} in debian/changelog due to {1}".format(self._version, err))


class NPMVersionUpdater(object):
    def __init__(self, repo_dir, version):
        """
        The module updates package.json under the directory of repository
        _repo_dir: the directory of the repository
        _version: the new version which is going to be updated to package.json
        """
        self._repo_dir = repo_dir
        self._version = version

    def package_exist(self):
        """
        check whether package.json exists under the repository
        return: True if it exist
                False
        """
        if os.path.isdir(self._repo_dir):
            for filename in os.listdir(self._repo_dir):
                if filename == "package.json":
                    return True
        return False

    def update_package_json(self):
        """
        add the version of package.json
        return: Ture if changelog is updated
                False, otherwise
        """
        package_exist = self.package_exist()
        if not package_exist:
            print "No package.json under {0}".format(self._repo_dir)
            return False
        try:
            print "start to update version of {0}".format(self._repo_dir)
            NPM.update_version(self._repo_dir, version=self._version)
            return True
        except Exception, e:
            raise RuntimeError("Failed to update the version of package.json under {0}\ndue to {1}"\
                               .format(self._repo_dir, e))


def parse_command_line(args):
    """
    Parse script arguments.
    :return: Parsed args for assignment
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir",
                        required=True,
                        help="Top level directory that stores all the cloned repositories.",
                        action="store")
    parser.add_argument("--version",
                        required=True,
                        help="the new release version",
                        action="store")
    parser.add_argument("--message",
                        help="the message which is going to be added to changelog",
                        action="store")

    parser.add_argument("--publish",
                        help="Push the new manifest to github",
                        action='store_true')
    parser.add_argument("--git-credential",
                        help="Git credential for CI services",
                        action="append")

    parsed_args = parser.parse_args(args)
    return parsed_args

def main():
    # parse arguments
    args = parse_command_line(sys.argv[1:])
    if args.publish:
        if args.git_credential:
            repo_operator = RepoOperator(args.git_credential)
        else:
            print "If you want to publish the updated changelog, please specify the git-credential. Exiting now..."
            sys.exit(1)

    if os.path.isdir(args.build_dir):
        for filename in os.listdir(args.build_dir):
            try:
                repo_dir = os.path.join(args.build_dir, filename)
                changelog_updater = ChangelogUpdater(repo_dir, args.version)
                npm_package_updater = NPMVersionUpdater(repo_dir, args.version)
                package_updated = npm_package_updater.update_package_json()
                changelog_updated = changelog_updater.update_changelog(message = args.message)
                if changelog_updated or package_updated:
                    if args.publish:
                        print "start to push changes in {0}".format(repo_dir)
                        commit_message = "jump version for new release {0}".format(args.version)
                        repo_operator.push_repo_changes(repo_dir, commit_message)
            except Exception,e:
                print "Failed to jump version of {0} due to {1}".format(filename, e)
                sys.exit(1)
    else:
        print "The argument build-dir must be a directory"
        sys.exit(1)

if __name__ == "__main__":
    main()
    sys.exit(0)
