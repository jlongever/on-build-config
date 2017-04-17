"""
This is a module that contains the tool for python to interact with our JFrog
artifactory API.
"""

import hashlib
import json
import os
import requests

class JFrogArtifactory(object):
    """
    This is a class that holds the interacting method for JFrog Artifactory
    """

    def __init__(self, user_cred,
                 artifactory_loc=
                 "http://afeossand1.cec.lab.emc.com/artifactory"):
        """
        Initialize this artifact interaction class
        :param artifactory_loc: the url for artifactory
        :param user_cred: the credential that is enough to execute the
            work required
        :return:
        """
        self.__artifactory_base = artifactory_loc
        self.__credential = user_cred
        self.__session = requests.session()
        self.__session.auth = self.__credential



    def __del__(self):
        """
        Object destroyer, close file IO and HTTP session handler on destroy
        :return:
        """
        self.__session.close()

    def __str__(self):
        """
        String representation of this class
        :return: "Interface to JFrog artifactory with {url}."
        """
        str = "Interface to JFrog artifactory at: {url}".\
            format(url=self.__artifactory_base)
        return str

    def get_package(self, repo_name, package_type, package_name):
        """
        Return the packages list with specific package name
        :param repo_name:  Artifactory Repo name
        :param package_type: example, for debian package, it's "deb"
        :param package_name: example, on-http
        """
        uri = "{uri_base}/api/search/prop?{pkg_type}.name={pkg_name}&repos={repo_name}".format(uri_base=self.__artifactory_base, pkg_type=package_type, pkg_name=package_name,repo_name=repo_name)

        response = self.__session.get(uri)
        if response.status_code != 200:
            print "Did not get a 200 in your request: ", uri
            return None

        list = response.json()

        #print "repo list is:\n{0}".format(list)
        return list


    def is_version_exist( self, repo_name, package_type, package_name, version_string ):
        """
        Check if a version for specific package exist, by checking remote file names
        """
        ret_json = self.get_package( repo_name, package_type, package_name )
        if ret_json is None:
            return False
        pkg_list = ret_json['results']
        desired_ver = package_name+"_"+version_string # this should align the package file name , instead of the version naming
        for p in pkg_list:
            if 'uri' in p.keys() :
                if desired_ver in str(p['uri']):
                   return True
        return False


    def get_repo_list(self):
        uri = "{uri_base}/api/repositories".format(uri_base=self.__artifactory_base)

        response = self.__session.get(uri)
        if response.status_code != 200:
            print "Did not get a 200 in your request: ", uri
            return None

        list = response.json()

        #print "repo list is:\n{0}".format(list)
        return list


    def get_artifactory_url(self):
        """
        Getter for artifactory base url
        :return: string based artifactory url
        """
        return self.__artifactory_base

    def repo_exists(self, rname):
        """
        Return the existence status of the named repository

        :param rname: name of the repo to check
        :return: True (if rname exists), False otherwise
        """
        repolist = self.get_repo_list();
        for repo in repolist:
            if 'key' in repo and repo['key'] == rname:
                return True

        return False


    def new_local_repo(self, rname, description, repo_type="debian"):
        """
        Creates a local repo at pre-given artifactory
        :param rname: repository name
        :param description: description of the artifactory
        :param repo_type: optional -- the type of artifactory
        default to debian
        :return: return response instance
                raise and return any other errors if encounters
        """
        dict_artifact_config = {
            "key": rname,
            "rclass": "local",
            "packageType": repo_type,
            "description": description,
            "enableDebianSupport": True,
            "snapshotVersionBehavior": "unique",
            "propertySets":["artifactory"]
            }

        uri = "{uri_base}/api/repositories/{repo_name}".format(
            uri_base=self.__artifactory_base, repo_name=rname)
        print "Trying to PUT\n{data}\nto\n{uri}.\n". \
            format(data=json.dumps(dict_artifact_config), uri=uri)

        try:
            response = self.__session.put(
                uri,
                data=json.dumps(dict_artifact_config),
                headers={"Content-Type": "application/json"}
            )
            if response.status_code != 200:
                print "Did not get a 200 in your request: "
        finally:
            print "Successfully created new repo at artifactory."

        return response

    def upload_one_file(self, file_path, repository, dir_path,distribution, component, architecture ):
        """
        This function uploads one file to target repository in artifactory.
        :param file_path: The path to the file to be uploaded
        :param repository: The repository folder name that the file
                            will be uploaded to
        :param dir_path: The directory path that will have in artifactory
                            repository

        :return: instance of response
        """
        if os.path.exists(file_path):
            file_name = os.path.basename(file_path)
        else:
            raise ValueError("The file path provided\n\t{path}\n"
                             "is not a file.".format(path=file_path))

        url = "{uri_base}/{rname}/{dir_path}/{fname}"\
            .format(uri_base=self.__artifactory_base, rname=repository,
                    dir_path=dir_path, fname=file_name)

        # Only let debians have metadata
        if file_path.endswith(".deb"):
            url += ";deb.distribution={dist};deb.component={comp};" \
                  "deb.architecture={arch};".format(dist=distribution, comp=component, arch=architecture)

        print "Trying to PUT\n{data}\n\tto\n{uri}".format(
            data=file_path, uri=url)

        try:
            with open(file_path, 'rb') as fp:
                file_data = fp.read()
        finally:
            fp.close()

        response = self.__session.put(url, file_data)
        if response.status_code != 201:
            print "Did not get a 201 (Successfully Created) in upload request: "
            return response

        # There is successfully created code returned, verify the hashcodes
        res_content = response.json()
        md5 = hashlib.md5(file_data).hexdigest()
        sha1 = hashlib.sha1(file_data).hexdigest()

        if res_content['checksums']['md5'] != md5 or \
            res_content['checksums']['sha1'] != sha1:
            raise ValueError(
                'Upload failure, the md5 or sha1 code returned'
                ' does not match the local version.')
        else:
            print "{file} is uploaded successfully.".format(file=file_name)

        return response

    def remove_repository(self, repo_name):
        """
        remove all the contents under repository.
        :param repo_name: the repository that will be deleted
        :return:
            instance of response
            Raise any exceptions if encountered
        """
        url = "{base}/api/repositories/{repo}"\
            .format(base=self.__artifactory_base, repo=repo_name)

        response = self.__session.delete(url)
        if response.status_code == 200:
            print "Repository {repo} deleted successfully."\
                .format(repo=repo_name)
        else:
            print "Did not delete the repository successfully."

        return response

