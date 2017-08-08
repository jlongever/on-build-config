#!/usr/bin/env python
# Copyright 2016, EMC, Inc.
"""
This is a command line program that upload a rackhd release to artifactory.
./on-tools/manifest-build-tools/HWIMO-BUILD on-tools/manifest-build-tools/application/release_debian_packages.py --build-directory b/ \
        --artifactory-credential artifactory \
        --artifactory-repo rackhd_staging \
        --artifactory-url  http://afeossand1.cec.lab.emc.com/artifactory \
        --artifactory-user username \
        --artifactory-password password \
        --deb-component staging \
        --deb-distribution trusty \
        --deb-architecture amd64 \
        --debian-depth 3
        The required parameters:
        build-directory: A directory where all the repositories are cloned to. 
        artifactory-credential: The environment variable name of artifactory credential.
                            For example: artifactory_CREDS=username:api_key

"""

import argparse
import os
import requests
import sys

from ArtifactoryTools  import JFrogArtifactory
from DebianToolsOnArtifactory import  DebianToolsOnArtifactory
from DebianToolsOnArtifactory import DebianErrorOnArtifactory


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


    parser.add_argument('--artifactory-username',
                        required=True,
                        help="artifactory credential for CI services: <Credentials>: User Name",
                        action='store')

    parser.add_argument('--artifactory-password',
                        required=True,
                        help="artifactory credential for CI services: <Credentials>: Password",
                        action='store')

    parser.add_argument('--artifactory-repo',
                        required=True,
                        help="the Artifactory repository name",
                        action='store')

    parser.add_argument('--artifactory-url',
                        required=True,
                        help="artifactory URL, like http://afeossand1.cec.lab.emc.com/artifactory",
                        action='store')

    parser.add_argument('--deb-component',
                        help="such as: main",
                        action='store',
                        default='staging')

    parser.add_argument('--deb-distribution',
                        help="such as: trusty, xenial",
                        action='store',
                        default='trusty')

    parser.add_argument('--deb-architecture',
                        help="such as: amd64, i386",
                        action='store',
                        default='amd64')

    parsed_args = parser.parse_args(args)
    return parsed_args



def make_debian_repo(repo_name, description, artifactory):
    """
    create an empty debian artifact repository when building step is executed
     successfully.
    :param repo_name: the name of the repository that will be created on
        jfrog artifactory
    :param description: the description for the created repository.
    :param artifactory: the artifactory object that will be used to create
        repository on

    :return:
        exit on failures
        none on success
    """
    print "[Info] Try make {repo} with\n {arti}".format(repo=repo_name, arti=str(artifactory))
    try:
        response = artifactory.new_local_repo(rname=repo_name,
                                              description=description)
        if response.status_code != 200:
            print "[Error] did not create repository successfully, got response code "\
                  "{code}. \n{detail}"\
                .format(code=response.status_code, detail=response.text)
            exit(3)
    except requests.requestexception as error:
        print "[Error] found error during request. details as below\n {err}"\
            .format(err=error)
        exit(3)
    else:
        print "[Info] repository {repo} created successful\n"\
            .format(repo=repo_name)


def upload_debs_to_artifactory(repo_name, top_level_dir, artifactory, depth, distribution, component, architecture ):
    """
    Upload all the debians under top level dir to given repository name
    :param repo_name: The repository name that the debian will be uploaded to
    :param top_level_dir: The top level directory that contains the debians to
        be uploaded to.
    :param artifactory: The artifactory tool with which the upload will be
        carried over.
    :param depth: How deep do you want this program to go into top-level-dir
     to look for debians to upload.

    :return:
        None on success.
        Exit on Errors
    """
    deb_tool = DebianToolsOnArtifactory(repo_name=repo_name,
                           top_dir_name=top_level_dir,
                           artifactory=artifactory,
                           distribution=distribution,
                           component=component,
                           architecture=architecture)
    if depth != 3:
        deb_tool.set_walk_depth(depth)

    print "[Info] Try upload all debians under {dir}".format(
        dir=deb_tool.get_top_dir())
    print deb_tool
    try:
        upload_result = deb_tool.upload_debs()
        if upload_result.is_good:
            print "\n[Info] All the debians are uploaded successfully."
            print upload_result.detail()
    except DebianErrorOnArtifactory as error:
        print "[Error] Error encountered when uploading the debs to artifactory:"
        print error
        exit(2)




def main():
    """
    Upload all the debian packages under top level dir to Artifactory.
    Exit on encountering any error.
    :return:
    """
    args = parse_args( sys.argv[1:] )
    try:
        artifactory_obj = JFrogArtifactory(
                                             user_cred=(args.artifactory_username, args.artifactory_password),
                                             artifactory_loc= args.artifactory_url  )

        if  False == artifactory_obj.repo_exists( args.artifactory_repo ): 
            # Create the remote repo if not exist
            description = "Repository made for staging debian packages."
            make_debian_repo( args.artifactory_repo , description, artifactory_obj)
        else:
            print "[Info] The remote repo {repo_name} already exist. Skip make_debian_repo step.".format(repo_name=args.artifactory_repo)

        #upload all the deb in top_level_dir, to artifactory
        upload_debs_to_artifactory( repo_name    = args.artifactory_repo,
                                    top_level_dir= args.build_directory,
                                    artifactory  = artifactory_obj,
                                    depth        = args.debian_depth,
                                    distribution = args.deb_distribution,
                                    component    = args.deb_component,
                                    architecture = args.deb_architecture )

    except Exception, e:
        print "[Exception Caught]",e
        sys.exit(1)

if __name__ == '__main__':
    main()

