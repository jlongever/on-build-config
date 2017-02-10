"""
clients class of ci/cd platforms: bintray, atlas, dockerhub ...
"""

import os
import sys
import requests
import subprocess
import base64
from dateutil import parser

try:
    import common
except ImportError as import_err:
    print import_err
    sys.exit(1)


class Atlas(object):
    """
    A simple class of atlas.
    An instance of 'class Atlas' represents a box in Atlas.
        default: rackhd/rackhd in official Atlas server.
    """
    def __init__(self, creds, atlas_url, atlas_name):
        # This class doesn't use user:pass format creds because 
        # just atlas_token is enough for call atlas API. 
        assert creds, "creds is None!"
        assert atlas_name, "atlas_name is None!"
        
        # creds can be a env varname of value "user:token" or just the value
        try:
            # get from env var
            self.atlas_username, self.atlas_token = common.parse_credential_variable(creds)
        except ValueError as e:
            # not in env var, parse as user:api-key
            self.atlas_username, self.atlas_token = creds.split(":")

        self.atlas_url = atlas_url or "https://atlas.hashicorp.com/api/v1"
        self.atlas_name = atlas_name
        self.box = "/".join(["box", self.atlas_username, self.atlas_name])

        self.session = requests.Session()
        self.session.headers.update({'X-Atlas-Token': self.atlas_token})

    def upload_handler(self, atlas_version, provider, box_file):
        """
        Upload a box file to atlas.
        See https://vagrantcloud.com/help/vagrant/boxes/create for more details
        """
        try:
            if not self.version_exist(atlas_version):
                self.create_version(atlas_version)

            if not self.provider_exist(atlas_version, provider):
                self.create_provider(atlas_version, provider)

            self.upload_box(atlas_version, provider, box_file)
            # release when upload is the present requirements
            self.release_box(atlas_version)
        except Exception as any_expection:
            raise Exception("Faild to upload box {0} to {1}/{2}\n{3}".format(box_file, atlas_version, provider, any_expection))

    def create_version(self, atlas_version):
        """
        Create box version
        """
        create_version_url = self.generate_url("create_version")
        version_data = {'version[version]': atlas_version}
        print create_version_url
        resp = self.session.post(create_version_url, data=version_data)
        if resp.ok:
            print "Create box version {0} successfully.".format(atlas_version)
        else:
            raise Exception("Failed to create box version.\n {0}".format(resp.text))

    def create_provider(self, atlas_version, provider):
        """
        Create box provider of a specific version
        """
        create_provider_url = self.generate_url("create_provider", atlas_version)
        provider_data = {'provider[name]': provider}
        resp = self.session.post(create_provider_url, data=provider_data)
        if resp.ok:
            print "Create box provider {0} of version {1} successfully.".format(provider, atlas_version)
        else:
            raise Exception("Failed to create box provider.\n {0}".format(resp.text))

    def upload_box(self, atlas_version, provider, box_file):
        """
        Upload one box to a specific version/provider
        """
        upload_box_url = self.generate_url("upload_box", atlas_version, provider)
        resp = self.session.get(upload_box_url)
        if resp.ok:
            upload_path = resp.json()["upload_path"]
            cmd = "curl -X PUT --upload-file " +  box_file  + " " +  upload_path
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            retval = p.wait()
            if retval == 0 :
                print "Upload box {0} to version/{1}/provider/{2} successfully!".format(box_file, atlas_version, provider)
            else:
                raise Exception("Failed to Upload box {0} to version/{1}/provider/{2}!\n {3}".format(box_file, atlas_version, provider,retval))

    def release_box(self, atlas_version):
        """
        Change the status of specific atlas_version to release
        """
        release_url = self.generate_url("release_box", atlas_version)
        resp = self.session.put(release_url)
        if resp.ok:
            print "Release version {0} successfully!".format(atlas_version)
        # Atlas return 422(Unprocessable Entity) when you try to release a released version.
        # Not sure if 422 is only for "already released" so add text-find double check.
        elif resp.text.find("already") != -1 and resp.status_code == 422:
            print "Warning: version {0} has already been released!".format(atlas_version)
        else:
            raise Exception("Failed to release version {0}\n{1}".format(atlas_version, resp.text))

    def version_exist(self, atlas_version):
        """
        Check if box version exists
        """
        check_version_url = self.generate_url("version", atlas_version)
        resp = self.session.get(check_version_url)
        if resp.ok:
            print "Box version {0} already exists.".format(atlas_version)
            return True
        print "Box version {0} doesn't' exist, will be created soon.".format(atlas_version)
        return False

    def provider_exist(self, atlas_version, provider):
        """
        Check if box provider exists.
        NOTICE: provider depends on a specific box version.
        """
        if not self.version_exist(atlas_version):
            print "Box version {0} doesn't' exist, please create version before check provider.".format(atlas_version)
            return False
        check_provider_url = self.generate_url("check_provider", atlas_version, provider)
        resp = self.session.get(check_provider_url)
        if resp.ok:
            print "{0} provider of version {1} already exists!".format(provider, atlas_version)
            return True
        print "{0} provider of version {1} doesn't' exist, will be created soon".format(provider, atlas_version)
        return False

    def get_box_versions(self):
        """
        Get all boxes' versions
        """
        get_box_versions_url = self.generate_url("box")
        resp = self.session.get(get_box_versions_url)
        if resp.ok:
            versions = [item["version"] for item in resp.json()["versions"]]
        else:
            raise Exception("Failed to get box versions {0}\n{1}".format(self.box, resp.text))
        return versions
    def get_box_versions_between_upload_time_range(self, begin_time, end_time):
        """
        Get boxes' versions build between begin_time and end_time
        """
        assert begin_time <= end_time, "end_time must larger than begin_time"
        versions_between_upload_time_range = []
        get_box_versions_url = self.generate_url("box")
        resp = self.session.get(get_box_versions_url)
        if resp.ok:
            for version_object in resp.json()["versions"]:
                upload_time = parser.parse(version_object["updated_at"])
                if begin_time < upload_time < end_time:
                    versions_between_upload_time_range.append(version_object["version"])
        else:
            raise Exception("Failed to get box {0} versions between {1} and {2} \n{3}".format(self.box, begin_time, end_time, resp.text))
        return versions_between_upload_time_range

    def del_box_version(self, version):
        """
        Delete one box version
        """
        del_box_versions_url = self.generate_url("version", version)
        resp = self.session.delete(del_box_versions_url)
        if resp.ok:
            print "Delete {0}/{1} successfully!".format(self.box, version)
        else:
            raise Exception("Failed to delete {0}/{1}\n{2}!".format(self.box, version, resp.text))

    def generate_url(self, purpose, atlas_version=None, provider=None):
        """
        Tool method, Generate all possible urls according to purpose
        """
        purpose_handler = {
            "version": "/".join([self.atlas_url, self.box, "version/{0}".format(atlas_version)]),
            "create_version": "/".join([self.atlas_url, self.box, "versions"]),
            "check_provider": "/".join([self.atlas_url, self.box, "version/{0}/provider/{1}".format(atlas_version, provider)]),
            "create_provider": "/".join([self.atlas_url, self.box, "version/{0}/providers".format(atlas_version)]),
            "upload_box": "/".join([self.atlas_url, self.box, "version/{0}/provider/{1}".format(atlas_version, provider), "upload"]),
            "release_box": "/".join([self.atlas_url, self.box, "version/{0}".format(atlas_version, provider), "release"]),
            "box": "/".join([self.atlas_url, self.box])
        }
        return purpose_handler[purpose]

class Bintray(object):
    """
    Bintray client for calling Bintray API.
    """
    def __init__(self, creds, subject, repo, push_executable=None, **kwargs):
        assert creds, "creds is None!"
        assert subject, "subject is None!"
        assert repo, "repo is None!"


        # creds can be a env varname of value "user:api_key" or just the value
        try:
            # get from env var
            self._username, self._api_key = common.parse_credential_variable(creds)
        except ValueError as e:
            # not in env var, parse as user:api-key
            self._username, self._api_key = creds.split(":")
        self._api_url = "https://api.bintray.com"
        self._subject = subject
        self._repo = repo

        self.session = requests.Session()
        basic_auth = "Basic {0}".format(base64.b64encode(":".join([self._username, self._api_key])))
        self.session.headers.update({'authorization': basic_auth})

        self._push_executable = push_executable
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def component(self):
        return self._component

    @component.setter
    def component(self, component):
        self._component = component

    @property
    def distribution(self):
        return self._distribution

    @distribution.setter
    def distribution(self, distribution):
        self._distribution = distribution

    @property
    def architecture(self):
        return self._architecture

    @architecture.setter
    def architecture(self, architecture):
        self._architecture = architecture

    def upload_a_file(self, package, version, file_path):
        """
        Upload a debian file to bintray.
        """
        cmd_args = [self._push_executable]
        cmd_args += ["--user", self._username]
        cmd_args += ["--api_key", self._api_key]
        cmd_args += ["--subject", self._subject]
        cmd_args += ["--repo", self._repo]
        cmd_args += ["--package", package]
        cmd_args += ["--version", version]
        cmd_args += ["--file_path", file_path]

        if self._component:
            cmd_args += ["--component", self._component]
        if self._distribution:
            cmd_args += ["--distribution", self._distribution]
        if self._architecture:
            cmd_args += ["--architecture", self._architecture]

        cmd_args += ["--package", package]
        cmd_args += ["--version", version]
        cmd_args += ["--file_path", file_path]

        try:
            common.run_command(cmd_args)
        except Exception, ex:
            raise RuntimeError("Failed to upload file {0} due to {1}".format(file_path, ex))
        return True

    def __get_package_version_object(self, package, version):
        """
        Get a version object of one package
        """
        version_object = {}
        package_version_url = "/".join([self._api_url, "packages", self._subject, self._repo, package, "versions", version])
        resp = self.session.get(package_version_url)
        if resp.ok:
            version_object = resp.json()
        else:
            raise Exception("Failed to get object of {0}/{1}\n {2}!".format(package, version, resp.text))
        return version_object

    def get_package_versions(self, package):
        """
        Get the version list of one package.
        """
        get_package_versions_url = "/".join([self._api_url, "packages", self._subject, self._repo, package])
        versions = []
        resp = self.session.get(get_package_versions_url)
        if resp.ok:
            versions = resp.json()["versions"]
        elif resp.status_code == 404:
            print "Bintray package: {0}/{1}/{2} doesn't exist".format(self._subject, self._repo, package)
        else:
            raise Exception("Failed to get package versions: {0}\n{1}".format(package, resp.text))
        return versions

    def del_package_version(self, package, version):
        """
        Delete a version of one package
        """
        del_package_version_url = "/".join([self._api_url, "packages", self._subject, self._repo, package, "versions", version])
        resp = self.session.delete(del_package_version_url)
        if resp.ok:
            print "Delete {0}/{1} successfully!".format(package, version)
        else:
            raise Exception("Failed to delete {0}/{1}\n {2}!".format(package, version, resp.text))

    def get_package_versions_between_upload_time_range(self, package, begin_time, end_time):
        """
        Get the version list of one package.
        """
        assert begin_time <= end_time, "end_time must larger than begin_time"
        versions_between_upload_time_range = []
        try:
            all_versions = self.get_package_versions(package)
            for version in all_versions:
                version_object = self.__get_package_version_object(package, version)
                upload_time = parser.parse(version_object["updated"])
                if begin_time < upload_time < end_time:
                    versions_between_upload_time_range.append(version)
        except Exception as e:
            raise Exception("Failed to get package {0} version between {1} and {2}.\n{3}".format(package, begin_time, end_time, e))
        return versions_between_upload_time_range


class Dockerhub(object):
    """
    A client class of Dockerhub.
    """
    def __init__(self, creds, repo, api_url):
        assert creds, "creds is None!"
        assert repo, "repo is None!"

        # creds can be a env varname of value "user:password" or just the value
        try:
            # get from env var
            self.username, self.password = common.parse_credential_variable(creds)
        except ValueError as e:
            # not in env var, parse as user:pass
            self.username, self.password = creds.split(":")
        self.repo = repo
        self.api_url = api_url or "https://hub.docker.com/v2"

        self.token = self.retrieve_token()
        self.session = requests.Session()
        self.session.headers.update({'authorization': "JWT %s" % self.token})

    def retrieve_token(self):
        """
        Get access token of dockerhub
        """
        login_url = "/".join([self.api_url, "users", "login"])
        data = {"username": self.username, "password": self.password}
        resp = requests.post(login_url, data=data)
        if resp.ok:
            return resp.json()["token"]
        else:
            raise Exception("Failed to retrive dockerhub token.\n{0}".format(resp.text))

    def __get_package_tags_objects(self, package):
        """
        Get all tags objects of a package
        """
        assert package, "arg package is None!"

        tags_objects = []
        get_package_versions_url = "/".join([self.api_url, "repositories", self.repo, package, "tags"])

        # dockerhub has paging mechanism
        next_page = get_package_versions_url
        while next_page:
            resp = self.session.get(next_page)
            next_page = None
            if resp.ok:
                resp_json = resp.json()
                tags_objects.extend(resp_json["results"])
                next_page = resp_json["next"]
            elif resp.status_code == 404:
                print "Package {0} does not exist.".format(package)
            else:
                raise Exception("Failed to get package tags objects: {0}\n{1}".format(package, resp.text))
        return tags_objects

    def get_package_tags(self, package):
        """
        Get all tags of a package
        """
        assert package, "arg package is None!"
        tags = []
        try:
            tags_objects = self.__get_package_tags_objects(package)
            for tag in tags_objects:
                tags.append(tag["name"])
        except Exception as e:
            raise Exception("Failed to get package tags: {0}\n{1}".format(package, e))
        return tags

    def get_package_tags_between_upload_time_range(self, package, begin_time, end_time):
        """
        Get tags of a package between date range
        """
        assert package, "arg package is None!"
        assert begin_time, "arg begin_time is None!"
        assert end_time, "arg end_time is None!"
        assert begin_time <= end_time, "end_time must larger than begin_time"

        tags_between_upload_time_range = []
        try:
            tags_objects = self.__get_package_tags_objects(package)
            
            for tag in tags_objects:
                upload_time = parser.parse(tag["last_updated"])
                if begin_time < upload_time < end_time:
                    tags_between_upload_time_range.append(tag["name"])
        except Exception as e:
            raise Exception("Failed to get package {0} tags between {1} and {2}: {0}\n{3}".format(package, begin_time, end_time, e))
        return tags_between_upload_time_range

    def del_package_tag(self, package, tag):
        """
        Del docker image of specific package/tag
        """
        assert package, "arg package is None!"
        assert tag, "arg tag is None!"
        del_package_versions_url = "/".join([self.api_url, "repositories", self.repo, package, "tags", tag])
        resp = self.session.delete(del_package_versions_url)
        if resp.ok:
            print "Delete {0}/{1} successfully!".format(package, tag)
        else:
            raise Exception("Failed to delete{0}/{1}.\n{2}".format(package, tag, resp.text))
