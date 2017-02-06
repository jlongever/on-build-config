"""
clients class of ci/cd platforms: bintray, atlas, dockerhub ...
"""

import os
import sys
import requests
import subprocess

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
    def __init__(self, atlas_url, atlas_username, atlas_name, atlas_token):
        self.atlas_url = atlas_url or "https://atlas.hashicorp.com/api/v1"

        self.atlas_username = atlas_username or "rackhd"
        self.atlas_name = atlas_name or "rackhd"
        self.box = "/".join(["box", self.atlas_username, self.atlas_name])

        self.atlas_token = atlas_token

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
            raise any_expection

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
        check_version_url = self.generate_url("check_version", atlas_version)
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

    def generate_url(self, purpose, atlas_version=None, provider=None):
        """
        Tool method, Generate all possible urls according to purpose
        """
        purpose_handler = {
            "check_version": lambda atlas_version, provider: "/".join([self.atlas_url, self.box, "version/{0}".format(atlas_version)]),
            "create_version": lambda atlas_version, provider: "/".join([self.atlas_url, self.box, "versions"]),
            "check_provider": lambda atlas_version, provider: "/".join([self.atlas_url, self.box, "version/{0}/provider/{1}".format(atlas_version, provider)]),
            "create_provider": lambda atlas_version, provider: "/".join([self.atlas_url, self.box, "version/{0}/providers".format(atlas_version)]),
            "upload_box": lambda atlas_version, provider: "/".join([self.atlas_url, self.box, "version/{0}/provider/{1}".format(atlas_version, provider), "upload"]),
            "release_box": lambda atlas_version, provider: "/".join([self.atlas_url, self.box, "version/{0}".format(atlas_version, provider), "release"])
        }
        return purpose_handler[purpose](atlas_version, provider)

class Bintray(object):
    """
    Bintray client for calling Bintray API.
    """
    def __init__(self, creds, subject, repo, push_executable, **kwargs):
        self._username, self._api_key = common.parse_credential_variable(creds)
        self._subject = subject
        self._repo = repo
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
