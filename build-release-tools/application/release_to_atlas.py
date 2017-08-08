#!/usr/bin/env python
# Copyright 2016, EMC, Inc.

"""
This is a command line program that upload vagrant.boxs to atlas.

usage:
    ./on-tools/manifest-build-tools/HWIMO-BUILD \
    on-tools/manifest-build-tools/application/release_to_atlas.py \
    --build-directory b/RackHD/packer \
    --atlas-url https://atlas.hashicorp.com/api/v1 \
    --atlas-creds rackhd:****** \
    --atlas-name rackhd \
    --atlas-version 1.2.3 \
    --is-release true

The required parameters:
    build-directory: A directory where box files laid in.
    atlas-creds: value or env var name of atlas creds, format is atlas_username:atlas_token.

The optional parameters:
    provider: The provider of vagrant box, virtualbox, vmware_fusion .etc, default: virtualbox
    atlas-url: Base URL for Atlas, default: https://atlas.hashicorp.com/api/v1
    atlas-name: The box name under a specific account of atlas, default: rackhd
    atlas-version: The box version in atlas, default: version number when is_release
                   0.month.day when is ci_builds.
"""

import sys
import argparse
import requests
import subprocess

try:
    import common
    from PlatformClients import Atlas
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
                        help="A directory where box files laid in",
                        action='store')

    parser.add_argument('--atlas-url',
                        help="Base URL for Atlas, default: https://atlas.hashicorp.com/api/v1",
                        action='store')

    parser.add_argument('--atlas-creds',
                        help="Value or env var name of atlas creds, format is atlas_username:atlas_token",
                        action='store')

    parser.add_argument('--atlas-name',
                        help="The repo name under a specific account of atlas, default: rackhd",
                        action='store')

    parser.add_argument('--atlas-version',
                        help="set box version in atlas",
                        action='store')

    parser.add_argument('--is-release',
                        help="if this is a step of rlease build",
                        default=False,
                        action='store')

    parsed_args = parser.parse_args(args)
    return parsed_args

def upload_boxs(build_directory, atlas, is_release, atlas_version):
    """
    The function will walk through all sub-folder under $build_directory, and for every *.box found:
        1. retrieve its version
        2. upload to atlas with this version
    NOTICE:
        1. Box version is calculated from box file name.
        2. Box provider is hardcoded and default to virtualbox currently.
           If need to upload boxs of multi-provider, there should be a way
           to pass the provider information to this script.
    """

    box_files = common.find_specify_type_files(build_directory, ".box", depth=1)
    if len(box_files) == 0:
        print "No box found under {0}".format(build_directory)

    for full_file_path in box_files:
        if not atlas_version:
            if is_release:
                # Box file name is like "rackhd-ubuntu-14.04-1.2.3.box" when release.
                # Extract 1.2.3 only
                atlas_version = full_file_path.split('/')[-1:][0].strip(".box").split('-')[3]
            else:
                from datetime import datetime
                import time
                datatime_now_md = time.strftime("0.%m.%d", time.gmtime(int(datetime.utcnow().strftime('%s')) - 24*60*60))
                atlas_version = datatime_now_md
            atlas.upload_handler(atlas_version, "virtualbox", full_file_path)


def main():
    """
    Upload all the vagrant boxs to Atlas.
    """
    try:
        args = parse_args(sys.argv[1:])
        is_release = False
        if args.is_release == "true" or args.is_release == "True":
            is_release = True
        atlas = Atlas(creds=args.atlas_creds, atlas_url=args.atlas_url, atlas_name=args.atlas_name)
        upload_boxs(args.build_directory, atlas, is_release, args.atlas_version)
    except Exception, e:
        print e
        sys.exit(1)

if __name__ == '__main__':
    main()
