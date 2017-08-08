#!/usr/bin/env python
# Copyright 2016, EMC, Inc.
"""
This is a command line program that upload a rackhd release to bintray.

./on-tools/manifest-build-tools/HWIMO-BUILD on-tools/manifest-build-tools/application/release_debian_packages.py --build-directory b/ \
--bintray-credential BINTRAY \
--bintray-subject rackhd \
--bintray-repo debian \
--bintray-component main \
--bintray-distribution trusty \
--bintray-architecture amd64 \
--debian-depth 3

The required parameters:
build-directory: A directory where all the repositories are cloned to. 
bintray-credential: The environment variable name of bintray credential.
                    For example: BINTRAY_CREDS=username:api_key
bintray-subject: The Bintray subject, which is either a user or an organization
bintray-repo: The Bintary repository name

The optional parameters:
component: The uploaded component of package, default: main
distribution: The uploaded distribution of package, default: trusty
architecture: The uploaded architecture of package, default: amd64
debian-depth: The depth in top level directory that you want this program look into to find debians.
"""
import argparse
import os
import sys

try:
    import common
    from PlatformClients import Bintray
except ImportError as import_err:
    print import_err
    sys.exit(1)

push_exe_script = "pushToBintray.sh"

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

    parser.add_argument('--debian-depth',
                        help="The depth in top level directory that you want"
                             " this program look into to find debians.",
                        default=3,
                        type=int,
                        action='store')

    parser.add_argument('--bintray-credential',
                        required=True,
                        help="bintray credential for CI services: <Credentials>",
                        action='store')

    parser.add_argument('--bintray-subject',
                        required=True,
                        help="the Bintray subject, which is either a user or an organization",
                        action='store')

    parser.add_argument('--bintray-repo',
                        required=True,
                        help="the Bintary repository name",
                        action='store')

    parser.add_argument('--bintray-component',
                        help="such as: main",
                        action='store',
                        default='main')

    parser.add_argument('--bintray-distribution',
                        help="such as: trusty, xenial",
                        action='store',
                        default='trusty')

    parser.add_argument('--bintray-architecture',
                        help="such as: amd64, i386",
                        action='store',
                        default='amd64')

    parsed_args = parser.parse_args(args)
    return parsed_args

def get_push_executable():
    repo_dir = os.path.dirname(sys.path[0])
    for subdir, dirs, files in os.walk(repo_dir):
        for file in files:
            if file == push_exe_script:
                return os.path.join(subdir, file)
    return None

def upload_debs(build_directory, debian_depth, bintray):
    """
    The function will walk through all sub-folder under $build_directory, and for every *.deb found:
        1. retrieve its version and package name
        2. upload to bintray with this version

    :param build_directory: The directory where all the build repositories are cloned.
    :param debian_depth: integer for level of directories to look into
                         the repository directory to look for debians
    :param bintray: An instance of Bintray.
    """
    return_dict_detail = {}
    debian_files = common.find_specify_type_files(build_directory, ".deb", depth=debian_depth)
    if len(debian_files) == 0:
        return_dict_detail[build_directory] = "No debians found under {dir}".format(dir=build_directory)

    for file_itr in debian_files:
        version = common.get_debian_version(file_itr)
        package = common.get_debian_package(file_itr)
        upload_result = bintray.upload_a_file(package, version, file_itr)
        if upload_result:
            return_dict_detail[package] = "{package} upload successfully".format(package=file_itr)
        else:
            raise RuntimeError("Upload Failure at {repo}.\nDetails:{file}: Fail"
                               .format(repo=package, file=file_itr))

    return return_dict_detail

def main():
    """
    Upload all the debian packages under top level dir to bintray.
    Exit on encountering any error.
    :return:
    """
    args = parse_args(sys.argv[1:])
    try:
        push_script_path = get_push_executable()
        bintray = Bintray(args.bintray_credential, args.bintray_subject, args.bintray_repo, push_script_path, component=args.bintray_component, distribution=args.bintray_distribution, architecture=args.bintray_architecture)

        return_dict_detail = upload_debs(args.build_directory, args.debian_depth, bintray)
        for key, value in return_dict_detail.items():
            print "{key}: {value}".format(key=key, value=value)
    except Exception, e:
        print e
        sys.exit(1)

if __name__ == '__main__':
    main()
