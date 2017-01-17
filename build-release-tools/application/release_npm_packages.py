#!/usr/bin/env python
# Copyright 2016, DELLEMC, Inc.

"""
This is a command line program that makes a rackhd release to npmjs.

Usage:
./on-build-config/build-release-tools/HWIMO-BUILD on-build-config/build-release-tools/application/release_npm_packages.py \
--build-directory b/ \
--manifest-file rackhd-devel \
--git-credential https://github.com,GITHUB \
--npm-credential registry.npmjs.org,6a2d8de2-dfce-4f59-a866-20f1baa394bd \
--jobs 8 \
--is-official-release true\
--force 

The required parameters:
build-directory: A directory where all the repositories are cloned to. 
manifest-file: The path of manifest file. 
npm-credential: NPM registry url and token for ci service: <URL>,<Token>

The optional parameters:
git-credential: Git URL and credential for CI services: <URL>,<Credentials>
is-official-release: Whether this release is official. The default value is False
force: Use destination directory, even if it exists.
jobs: Number of parallel jobs(build debian packages) to run.
      The number is related to the compute architecture, multi-core processors..
"""

import argparse
import os
import sys
import json

try:
    from reprove import ManifestActions
    from version_generator import VersionGenerator
    from npm import NPM
    import common
except ImportError as import_err:
    print import_err
    sys.exit(1)

def parse_args(args):
    """
    Parse script arguments.
    :return: Parsed args for assignment
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-directory',
                        required=True,
                        help="Top level directory that stores all the cloned repositories.",
                        action='store')

    parser.add_argument('--manifest-file',
                        required=True,
                        help="The file path of manifest",
                        action='store')

    parser.add_argument('--git-credential',
                        help="Git URL and credential for CI services: <URL>,<Credentials>",
                        action='append',
                        default=None)

    parser.add_argument('--npm-credential',
                        required=True,
                        help="NPM URL and credential for CI services: <URL>,<Token>",
                        action='store')

    parser.add_argument('--jobs',
                        help="Number of build jobs to run in parallel",
                        default=-1,
                        type=int,
                        action="store")

    parser.add_argument('--is-official-release',
                        default="false",
                        help="Whether this release is official",
                        action="store")

    parser.add_argument('--force',
                        help="Overwrite a directory even if it exists",
                        action="store_true")

    parsed_args = parser.parse_args(args)
    parsed_args.is_official_release = common.str2bool(parsed_args.is_official_release)
    return parsed_args

def get_npm_packages(build_dir):
    '''
    Find all the packages which contains package.json under the directory specified by the parameter build_dir
    '''
    packages = []
    for dirname in os.listdir(build_dir):
        repo_dir = os.path.join(build_dir,dirname)
        if os.path.isdir(repo_dir):
            for filename in os.listdir(repo_dir):
                if filename == "package.json":
                    packages.append(dirname)
                    break
    return packages

def compute_packages_version(build_dir, is_official_release):
    '''
    compute the version of packages under the build_dir
    return: a dict like: {"package name": "version"}
    '''
    version_dict = {}
    try:
        npm_packages = get_npm_packages(build_dir)
        for package in npm_packages:
            package_dir = os.path.join(build_dir, package)
            version_generator = VersionGenerator(package_dir)
            version = version_generator.generate_package_version(is_official_release, version_type="npm")
            if version != None:
                version_dict[package] = version
            else:
                raise RuntimeError("Failed to compute version of {package} due to version is None".format(package=package_dir))
        return version_dict

    except Exception, e:
        raise RuntimeError("Failed to compute version for packages under {0} \ndue to {1}".format(build_dir, e))
    
def update_packages_version(build_dir, version_dict):
    """
    Update the package.json with the version
    :param build_dir: The directory of rackhd repository
    :param version_dict: a dict contains package name and version
    """
    try:
        for key, value in version_dict.iteritems():
            package_dir = os.path.join(build_dir, key)
            print "starting to update version of {0} to {1}".format(package_dir, value)
            NPM.update_version(package_dir, version=value)
    except Exception, e:
        raise RuntimeError("Failed to update version for package under {0} \ndue to {1}".format(build_dir, e))

def update_packages_dependency(build_dir, version_dict):
    """
    Update the dependency of package.json.
    For example:
    - "on-core": "git+https://github.com/RackHD/on-core.git",
    + "on-core": "1.0.0",
    """
    try:
        for key, value in version_dict.items():
            package_dir = os.path.join(build_dir, key)
            print "starting to update the dependency of {0}".format(package_dir)
            update_dependency(package_dir, version_dict)
    except Exception, e:
        raise RuntimeError("Failed to update dependency for package under {0} \ndue to {1}".format(build_dir, e))


def update_dependency(package_dir, version_dict):
    package_json_file = os.path.join(package_dir, "package.json")
    if not os.path.exists(package_json_file):
        # If there's no package.json file, there is nothing more for us to do here
        return

    changes = False
    log = ""
    with open(package_json_file, "r") as fp:
        package_data = json.load(fp)
        if "dependencies" in package_data:
            for package, version in package_data["dependencies"].items():
                new_version = None
                if package in version_dict:
                    new_version = version_dict[package]
                if new_version is not None and version != new_version:
                    package_data["dependencies"][package] = new_version
                    changes = True
                    log += "  {0}:\n    WAS {1}\n    NOW {2}\n".format(package,version,new_version)

    if changes:
        print "There are changes to dependencies for {0}\n{1}".format(package_json_file, log)
        os.remove(package_json_file)
        new_file = package_json_file
        with open(new_file, "w") as newfile:
            json.dump(package_data, newfile, indent=4, sort_keys=True)
    else:
        print "There are NO changes to data for {0}".format(package_json_file)

def publish_packages(build_dir, is_official_release, npm_registry, npm_token):
    """
    Publish all the npm packages under directory specified by build_dir
    """
    npm_packages = get_npm_packages(build_dir)
    # Skip the release of di.js
    npm_packages.remove("di.js")
    for package in npm_packages:
        try:
            package_dir = os.path.join(build_dir, package)
            npm = NPM(npm_registry, npm_token)
            print "starting to publish npm package {0}".format(package)
            if is_official_release:
                npm.publish_package(package_dir)
            else:
                npm.publish_package(package_dir, tag="ci-release")
        except Exception, e:
            if e.message.find("You cannot publish over the previously published version") != -1:
                print "The version of the package {0} is already published".format(package)
                pass
            else:
                raise RuntimeError("Failed to publish packages under {0} \ndue to {1}".format(build_dir, e))


def checkout_repos(manifest, builddir, force, jobs, git_credential=None):
    try:
        manifest_actions = ManifestActions(manifest, builddir, force=force, git_credentials=git_credential, jobs=jobs, actions=["checkout"])
        manifest_actions.execute_actions()
    except Exception, e:
        print "Failed to checkout repositories according to manifest file {0} \ndue to {1}. Exiting now...".format(manifest, e)
        sys.exit(1)


def main():
    """
    Publish all the npm packages
    Exit on encountering any error.
    """
    args = parse_args(sys.argv[1:])
    npm_registry, npm_token = args.npm_credential.split(',', 2)
    checkout_repos(args.manifest_file, args.build_directory, args.force, args.jobs, git_credential=args.git_credential)

    version_dict = compute_packages_version(args.build_directory, args.is_official_release)
    update_packages_version(args.build_directory, version_dict)
    update_packages_dependency(args.build_directory, version_dict)
    publish_packages(args.build_directory, args.is_official_release, npm_registry, npm_token)

if __name__ == '__main__':
    main()
