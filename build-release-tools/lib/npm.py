# Copyright 2017, DELLEMC, Inc.

"""
Module to abstract NPM operation
"""
import json
import sys
import os

try:
    import common
except ImportError as import_err:
    print import_err
    sys.exit(1)

class NPM(object):
    """
    A module of NPM
    """
    def __init__(self, registry, token):
        self._registry = registry
        self._token = token
        self.authenticate()

    def authenticate(self):
        '''
        Authenticate the npm registry with token
        '''
        try:
            home = os.path.expanduser("~")
            user_config = os.path.join(home,".npmrc")
            f = open(user_config, 'w+')
            text = "//{registry}/:_authToken={token}"\
                   .format(registry=self._registry, token=self._token)
            f.write(text)
            f.close()
            cmd_args = ['npm', 'whoami']
            common.run_command(cmd_args)
        except Exception, e:
            raise ValueError("Failed to authenticate with {registry} due to {error}"\
                             .format(registry=self._registry, error=e))

    @staticmethod
    def get_current_version(package_dir):
        """
        Get the version field in package.json
        """
        try:
            package_json_file = os.path.join(package_dir, "package.json")
            if not os.path.exists(package_json_file):
                # if there's no package.json file, there is nothing more for us to do here
                return None
            with open(package_json_file, "r") as fp:
                package_data = json.load(fp)
                fp.close()
                version = package_data["version"]
                return version
        except Exception, e:
            raise ValueError("Failed to get the version of package {package} due to {error}"\
                             .format(package=package_dir, error=e))

    @staticmethod
    def update_version(package_dir, version=None):
        '''
        update version of package
        '''
        try:
            cmd_args = ["npm", "version", "--no-git-tag-version"]
            if version is not None:
                cmd_args.append(version)
            common.run_command(cmd_args, directory=package_dir)
        except Exception, e:
            raise ValueError("Failed to update version of package {package} due to {error}"\
                             .format(package=package_dir, error=e))

    def publish_package(self, package_dir, tag=None):
        '''
        publish package to npm registry with tag
        '''
        try:
            cmd_args = ["npm", "publish"]
            if tag is not None:
                cmd_args += ["--tag", tag]
            common.run_command(cmd_args, directory=package_dir)
        except Exception, e:
            raise ValueError("Failed to publish package {package} due to {error}"\
                             .format(package=package_dir, error=e))
