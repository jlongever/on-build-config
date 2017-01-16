#!/usr/bin/env python

"""
Nightly build will only be stored for two weeks.
This is a command line program that clean up the overdue nightly builds.

NOTE:
The release build will never be deleted by this script.
because 
get_build_date_from_version() will return NULL for bintray/dockerhub sub routine, and "continue" to skip deletion.
for vagrant,  release build starts from 1. and old builds are only two digit(0.1x), so the sub-routine will skip the deletion also.

usage:
    ./on-build-config/build-release-tools/HWIMO-BUILD on-build-config/build-release-tools/application/nightly_build_clean_up.py
    --source-type bintray(dockerhub, atlas)
    --date-range 20170102-20170116
    # args for bintray
    --bintray-cred rackhdci:*****
    --bintray-subject rackhd
    --bintray-repo debian
    # args for dockerhub
    --dockerhub-cred rackhdci:p0ssw0rd
    --dockerhub_repo rackhd
    # args for atlas
    --atlas-url https://atlas.hashicorp.com/api/v1
    --atlas-cred rackhd:*****
    --atlas-name rackhd

The required parameters:
    source-type: The source of this operation will clean up.
    # for bintray
    bintray-cred: user:api-key of bintray, value or env var name.
    bintray-subject: The target subject you want to clean. Default: rackhd
    bintray-repo: Repo of the subject you want to clean. Default: debian
    # for dockerhub
    dockerhub-cred: user:pass, value or env var name.
    dockerhub-repo: Images to be cleaned in which Repo.
    # for atlas
    atlas-cred: user:token of atlas, value or env var name.
    atlas-username: The account name of atlas, default: rackhd
    atlas-name: The box name under a specific account of atlas, default: rackhd

The optional parameters:
    date_range: Specify beginTime-endTime of the nightly builds, default: last 14 days
    # for dockerhub
    dockerhub-api-url: Base API URL for dockerhub, default: "https://hub.docker.com/v2"
    # for atlas
    atlas-url: Base URL for Atlas, default: https://atlas.hashicorp.com/api/v1
"""

import sys
import argparse
import requests
import time
from datetime import datetime

try:
    import common
    from PlatformClients import Atlas, Bintray, Dockerhub
except ImportError as import_err:
    print import_err
    sys.exit(1)

def parse_args(args):
    """
    Parse script arguments.
    :return: Parsed args for assignment
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('--source-type',
                        required=True,
                        help="The source of this operation will clean up.",
                        action='store')

    parser.add_argument('--date-range',
                        help="Specify beginTime-endTime of the nightly builds, format:20170101-20170115, default: last 14 days",
                        action='store')

    parser.add_argument('--bintray-cred',
                        help="user:api-key of bintray.",
                        action='store')

    parser.add_argument('--bintray-subject',
                        help="The target subject you want to clean. Default: rackhd",
                        action='store')

    parser.add_argument('--bintray-repo',
                        help="Repo of the subject you want to clean. Default: debian",
                        action='store')

    parser.add_argument('--dockerhub-cred',
                        help="user:pass or just a ***** token.",
                        action='store')

    parser.add_argument('--dockerhub-repo',
                        help="Images to be cleaned in which Repo.",
                        action='store')

    parser.add_argument('--dockerhub-api-url',
                        help="Base API URL for dockerhub.",
                        action='store')

    parser.add_argument('--atlas-cred',
                        help="user:token of atlas.",
                        action='store')

    parser.add_argument('--atlas-url',
                        help="Base URL for Atlas, default: https://atlas.hashicorp.com/api/v1",
                        action='store')

    parser.add_argument('--atlas-name',
                        help="The repo name under a specific account of atlas, default: rackhd",
                        action='store')

    parsed_args = parser.parse_args(args)
    return parsed_args

RACKHD_REPOS = ["on-imagebuilder", "on-core", "on-syslog", "on-dhcp-proxy", "files", \
                "on-tftp", "on-wss", "on-statsd", "on-tasks", "on-taskgraph", "on-http"]

def clean_bintray_nightly_builds(bintray_cred, bintray_subject, bintray_repo, date_range):
    """
    clean bintray nightly builds
    """
    bintray = Bintray(creds=bintray_cred, subject=bintray_subject, repo=bintray_repo)
    for package in RACKHD_REPOS:
        versions = bintray.get_package_versions(package)
        for version in versions:
            build_date = get_build_date_from_version(package, version)
            if not build_date:
                continue
            if date_range[0] <= build_date <= date_range[1]:
                print "Cleaning {0}/{1} in bintray".format(package, version)
                bintray.del_package_version(package, version)
    print "Bintray nightly builds between {0} and {1} has been cleaned successfully".format(date_range[0], date_range[1])

def clean_dockerhub_nightly_builds(dockerhub_cred, dockerhub_repo, dockerhub_api_url, date_range):
    """
    clean dockerhub nightly builds
    """
    dockerhub = Dockerhub(creds=dockerhub_cred, repo=dockerhub_repo, api_url=dockerhub_api_url)
    for package in RACKHD_REPOS:
        tags = dockerhub.get_package_tags(package)
        # for rackhd docker images, version==tag
        for tag in tags:
            build_date = get_build_date_from_version(package, tag)
            if not build_date:
            # for release build versioned X.Y.Z , the build_date will be NULL
                continue
            if date_range[0] <= build_date <= date_range[1]:
                print "Cleaning {0}/{1} in dockerhub".format(package, tag)
                dockerhub.del_package_tag(package, tag)
    print "Dockerhub nightly builds between {0} and {1} has been cleaned successfully".format(date_range[0], date_range[1])

def clean_atlas_nightly_builds(atlas_cred, atlas_name, atlas_url, date_range):
    """
    clean atlas nightly builds
    """
    # atlas_token is enough for calling api, so split atlas_cred
    atlas = Atlas(creds=atlas_cred, atlas_name=atlas_name, atlas_url=atlas_url)
    versions = atlas.get_box_versions()
    # daliy build box version is like 0.12.25: 0.m.d
    #begin delete
    this_year = datetime.now().year
    this_month = datetime.now().month
    today = datetime.now().day
    last_year = datetime.now().year -1
    for version in versions:
        version_segments = [i for i in version.split(".")]
        if len(version_segments) < 3:
        # atlas support version like 0.16 , but nightly builds are all 0.x.y 
            continue
        y, m, d = version_segments
        if int(y) == 0:
        # nightly builds are all 0.x.y, initial number is 0
            if (int(m) > this_month) or (int(d) > today and  int(m) == this_month):
                build_date = int("".join([str(last_year), str(m), str(d)]))
            else:
                build_date = int("".join([str(this_year), str(m), str(d)]))
            if date_range[0] <= build_date <= date_range[1]:
                print "Cleaning box {0} in atlas".format(version)
                atlas.del_box_version(version)
    print "Atlas nightly builds between {0} and {1} has been cleaned successfully".format(date_range[0], date_range[1])


def get_date_range(date_range):
    """
    arg date_range is like "20170112-20170120"
    return: (20170112, 20170120)
    """
    if date_range:
        try:
            processed_date_range = tuple([int(i) for i in date_range.split('-')])
        except TypeError as e:
            print "Wrong format of date-range".fomat(e.message)
            sys.exit(1)
    else:
        # if no arg date_range, set date_range as the last 14 days
        begin_time = time.strftime("%Y%m%d", time.gmtime(time.time()-24*60*60*14))
        end_time = time.strftime("%Y%m%d", time.gmtime(time.time()))
        processed_date_range = (int(begin_time), int(end_time))

    return processed_date_range

def get_build_date_from_version(package, version):
    """
    extract build date from package version
    1.2.3-20161228UTC-5a1749a -> 20161228
    """
    version_segments = version.split("-")
    if len(version_segments) <= 1:
        # is release builds
        return
    try:
        build_date = int(version_segments[1].strip("UTC"))
    except Exception as e:
        # IndexError or ValueError
        print "Package version format error: {0}{1}\n {2}".format(package, version, e)
        #sys.exit(1)
        return
    # make sure build date is valid
    if build_date < 20000000 or build_date > 29999999:
        print "Package version format error: {0}{1}".format(package, version)
    return build_date


def main():
    """
    Clean nightly builds
    """
    try:
        args = parse_args(sys.argv[1:])
        source_type = args.source_type.lower()
        date_range = get_date_range(args.date_range)
        if source_type == "bintray":
            clean_bintray_nightly_builds(args.bintray_cred, args.bintray_subject, args.bintray_repo, date_range)
        elif source_type == "dockerhub":
            clean_dockerhub_nightly_builds(args.dockerhub_cred, args.dockerhub_repo, args.dockerhub_api_url, date_range)
        elif source_type == "atlas":
            clean_atlas_nightly_builds(args.atlas_cred, args.atlas_name, args.atlas_url, date_range)
        else:
            print "Wrong source-type arg: {0}\n source-type must be bintray, dockerhub or atlas".format(source_type)

    except Exception, e:
        print e
        sys.exit(1)

if __name__ == '__main__':
    main()
