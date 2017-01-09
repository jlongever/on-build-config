#!/usr/bin/env python
# Copyright 2015-2016, EMC, Inc.

"""
The script compute the version of a package, just like:
1.1.1-20161129UTC

usage:
./on-tools/manifest-build-tools/HWIMO-BUILD on-tools/manifest-build-tools/application/version_generator.py \
--repo-dir /home/onrack/rackhd/release/rackhd-repos/PengTian0/b/b/on-http \
--is-official-release true

Because this script need to import scripts under lib.
The script HWIMO-BUILD helps to add the scripts under lib to python path.

The required parameters: 
repo-dir: the directory of the repository

The optional parameters:
is-official-release: whether the release is official (default value is false)
"""
import os
import json
import sys
import argparse
from datetime import datetime,timedelta

try:
    from RepositoryOperator import RepoOperator
    import common
except ImportError as import_err:
    print import_err
    sys.exit(1)

class VersionGenerator(object):
    def __init__(self, repo_dir):
        """
        This module compute the version of a repository
        The version for candidate release: {release_version}-{build_version}
        The release version is parsed from debian/changelog
        The samll version is consist of the commit hash and commit date of manifest repository
        :return:None
        """
        self._repo_dir = repo_dir
        self.repo_operator = RepoOperator()
        self._repo_name = self.get_repo_name()

    def get_repo_name(self):
        repo_url = self.repo_operator.get_repo_url(self._repo_dir)
        repo_name = common.strip_suffix(os.path.basename(repo_url), ".git")
        return repo_name

    def generate_build_version(self):
        """
        Generate the build version which consists of commit date and commit hash of manifest repository
        According to build version, users can track the commit of all repositories in manifest file
        return: build version 
        """
        if self._repo_name == "RackHD":
            utc_now = datetime.utcnow()
            utc_yesterday = utc_now + timedelta(days=-1)
            version = utc_yesterday.strftime('%Y%m%dUTC')
            return version
        else:
            commit_timestamp_str = self.repo_operator.get_lastest_commit_date(self._repo_dir)
            date = datetime.utcfromtimestamp(int(commit_timestamp_str)).strftime('%Y%m%dUTC')
            commit_id = self.repo_operator.get_lastest_commit_id(self._repo_dir)
            version = "{date}-{commit}".format(date=date, commit=commit_id[0:7])
            return version

    def debian_exist(self):
        """
        check whether debian or debianstatic directory under the repository
        return: True if debian or debianstatic exist
                False
        """
        if os.path.isdir(self._repo_dir):
            for filename in os.listdir(self._repo_dir):
                if filename == "debian":
                    return True
        return False

    def generate_debian_release_version(self):
        """
        Generate the release version according to changelog
        The release version is the latest version of debian/changelog
        return: release version
        """
        # If the repository has the debianstatic/repository name/,
        # create a soft link to debian before compute version
        debian_exist = self.debian_exist()
        linked = False
        if not debian_exist:
            for filename in os.listdir(self._repo_dir):
                if filename == "debianstatic":
                    debianstatic_dir = os.path.join(self._repo_dir, "debianstatic")
                    for debianstatic_filename in os.listdir(debianstatic_dir):
                        if debianstatic_filename == self._repo_name:
                            debianstatic_repo_dir = "debianstatic/{0}".format(self._repo_name)
                            common.link_dir(debianstatic_repo_dir, "debian", self._repo_dir)
                            linked = True
        if not debian_exist and not linked:
            return None
        cmd_args = ["dpkg-parsechangelog", "--show-field", "Version"]
        version = common.run_command(cmd_args, directory=self._repo_dir)

        if linked:
            os.remove(os.path.join(self._repo_dir, "debian"))

        return version

    def generate_npm_release_version(self):
        """
        Generate the release version according to the version field in package.json
        """
        package_json_file = os.path.join(self._repo_dir, "package.json")
        if not os.path.exists(package_json_file):
            # if there's no package.json file, there is nothing more for us to do here
            return None
        with open(package_json_file, "r") as fp:
            package_data = json.load(fp)
            fp.close()     
            version = package_data["version"]
            return version

    def generate_package_version(self, is_official_release, version_type="debian"):
        """
        Generate the version of package, just like:
        1.1.1-20160809150908UTC-7396d91 or 1.1.1
        :return: package version
        """
        
        if version_type == "debian":
            release_version = self.generate_debian_release_version()
        elif version_type == "npm":
            release_version = self.generate_npm_release_version()
        else:
            common.logging.error("The parameter version_type {0} is not valid".format(version_type))
            common.logging.error("The parameter version_type can only be debian or npm")
            return None

        if release_version is None:
            common.logging.warning("Failed to generate release version, maybe the {0} doesn't contain debian directory or package.json".format(self._repo_dir))
            return None

        if is_official_release:
            version = release_version
        else:
            build_version = self.generate_build_version()
            if build_version is None:
                raise RuntimeError("Failed to generate version for {0}, due to the build version is None".format(self._repo_dir))

            version = "{0}-{1}".format(release_version, build_version)
        
        return version

def parse_command_line(args):
    """
    Parse script arguments.
    :return: Parsed args for assignment
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-dir",
                        required=True,
                        help="the directory of repository",
                        action="store")

    parser.add_argument('--is-official-release',
                        default="false",
                        help="Whether this release is official",
                        action="store")

    parsed_args = parser.parse_args(args)
    parsed_args.is_official_release = common.str2bool(parsed_args.is_official_release)
    return parsed_args

def main():
    # parse arguments
    args = parse_command_line(sys.argv[1:])
    generator = VersionGenerator(args.repo_dir)
    try:
        version = generator.generate_package_version(args.is_official_release)
        print version
    except Exception, e:
        common.logging.error("Failed to generate version for {0} due to {1}\n Exiting now".format(args.repo_dir, e))
        sys.exit(1)

if __name__ == "__main__":
    main()
    sys.exit(0)
