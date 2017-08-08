"""
This is a directory tool that contains the tool that uploads built debians
 to the Artifactory.
"""

import os
import requests

try:
    from ArtifactoryTools import JFrogArtifactory
    from resultTool import RepositoryResult
except ImportError as import_err:
    print import_err
    exit(1)

class DebianToolsOnArtifactory(object):
    """
    A class that holds the tools that checks the debian and upload them to
     correct repository.
    """
    def __init__(self, repo_name, top_dir_name, artifactory, distribution="trusty", component="main", architecture="amd64"):
        """
        Initializer of all the class variables.

        :param repo_name: The repository that is already built on the
            artifactory.
        :param top_dir_name: The directory where all the build repositories
            are cloned.
        :param artifactory: the artifactory instance of ArtifactoryTools

        :return: None on success.
        """
        self.set_repo_name(repo_name)
        self.set_top_dir(top_dir_name)
        self.set_artifactory(artifactory)
        self.set_walk_depth(3)
        self.set_debian_property( {"distribution":distribution,
                                   "component":component,
                                   "architecture":architecture} )

    def __str__(self):
        """
        String representation of this class
        :return: "Debian processor that uploads debians under\n {top_level_dir}
         \nto\n{repository} \nat\n {artifact_loc}\n"
        """
        str = "Debian uploader work on {top_dir} \nto\n" \
              "{rname} \n at \n {art_loc}\n"\
            .format(top_dir=self.__top_dir, rname=self.__repo_name,
                    art_loc=self.__artifactory.get_artifactory_url())
        return str


    def get_debian_property(self):
        """
        Getter of the debian package property
        return: map based property list
        """
        return self.__deb_property

    def set_debian_property(self, property_list ):
        """
        Setter for the debian package property
        :param property_list  : the "distribution","component","architecture" proprety of the debian packages
        :return None on success
        """
        self.__deb_property = property_list

    def get_repo_name(self):
        """
        Getter of the repository name.
        :return: string based repository name to upload to.
        """
        return self.__repo_name

    def get_top_dir(self):
        """
        Getter of the top level directory.
        :return: string based top level directory that it will work on.
        """
        return self.__top_dir

    def set_repo_name(self, repo_name):
        """
        Setter for the repository name
        :param repo_name: The repository that is already built on the
            artifactory.

        :return: None on success
        """
        self.__repo_name = repo_name

    def set_top_dir(self, top_dir_name):
        """
        Setter for top level dir
        :param top_dir_name: The directory where all the build repositories
            are cloned.

        :return: None on success.
        """
        self.__top_dir = os.path.abspath(top_dir_name)

    def set_artifactory(self, artifactory):
        """
        Setter of the artifactory
        :param artifactory: the instance of Artifactory Tools
        :return: None on success
        """
        if isinstance(artifactory, JFrogArtifactory):
            self.__artifactory = artifactory
        else:
            raise ValueError("artifactory should be an instance of Artifactory"
                             " Tools")

    def set_walk_depth(self, depth):
        """
        Set how deep you want the DebianTools to look into the top-level-dir
         to look for debians

        :param depth: integer for level of directories to look into.
        :return: None on success
        """
        if depth > 0:
            self.__walk_depth = depth
        else:
            raise ValueError("Please provide a positive integer for how depth "
                             "do you want DebianTool to look into the top "
                             "level directory")

    def __upload_a_deb(self, deb_path):
        """
        Uploads a debian after encountered.
        :param deb_path: absolute path of the debian file
        :return: boolean is_good
                True on successfully uploaded the debian file to artifactory.
                False on otherwise
        """
        file_name = os.path.basename(deb_path)
        repo_path = 'pool/'+file_name[0]
        try:
            response = self.__artifactory.upload_one_file(
                deb_path,
                self.__repo_name,
                repo_path,
                self.__deb_property["distribution"],
                self.__deb_property["component"],
                self.__deb_property["architecture"]  )

            if response.status_code == 201:
                print "status:{code}\ndetail:{detail}\n"\
                    .format(code=response.status_code, detail=response.text)
        except (IOError, ValueError, requests.RequestException) as err:
            print "Error encountered during the uploading."
            print err
            return False

        return True

    def __upload_debs_in_a_repo(self, dir_repo):
        """
        Upload the debian under one repository directory.

        It assumes that if a debian exists in the folder, then it must be
        a successful build.

        :param dir_repo: the location where the repository is cloned and the
         debian(s) is/are built inside

        :return:
            (return_is_success, return_dict_detial)
            return_is_success = True/False
            return_dict_detail = {
                <found_debian_name> : "Success"/"Fail"
                                }
                or {} if no debian is found.
        """
        return_is_success = True
        return_dict_detail = {}
        has_deb = False
        top_dir_depth = dir_repo.count(os.path.sep) #How deep is at starting point
        for root, dirs, files in os.walk(dir_repo, topdown=True):
            root_depth = root.count(os.path.sep)
            if (root_depth - top_dir_depth) <= self.__walk_depth:
                for file_itr in files:
                    if file_itr.endswith(".deb"):
                        has_deb = True
                        abs_file = os.path.abspath(os.path.join(root, file_itr))
                        file_name = os.path.basename(file_itr)

                        if self.__upload_a_deb(abs_file) is False:
                            return_dict_detail[file_name] = "Fail"
                            return_is_success = False
                        else:
                            return_dict_detail[file_name] = "Success"
   
            else:
                dirs = [] # Stop iteration

        if not has_deb:
            print "No debians found under {dir}".format(dir=dir_repo)

        return return_is_success, return_dict_detail

    def upload_debs(self):
        """
        Iterate through the top-level-dir and check if there is debian
        successful made then upload it to self.__repo_name and put it
        under corresponding folder (/pool/<initial_alphabet>/).

        It assumes that if a debian exists in the folder, then it is
        a successful build. This code will not be called unless all the
        per-directory build and test steps are succeed.

        :return:
            Instance of result class with a short is_success and a detail
             dictionary here.
            Raise other exceptions if encountered.
        """
        os.chdir(self.__top_dir)
        repo_list = os.listdir(self.__top_dir)
        print "Find following list of repository directories under {top}:" \
              "{dir_list}".format(top=self.__top_dir, dir_list=repo_list)
        return_is_okay = True
        return_dict_detail = {}

        for repo_itr in repo_list:
            absp_repo = os.path.abspath(repo_itr)
            repo_name = os.path.basename(repo_itr)
            print "Checking {rname} at {pname}"\
                .format(rname=repo_name, pname=absp_repo)
            (itr_is_okay, itr_dict_detail) = \
                self.__upload_debs_in_a_repo(absp_repo)
            if itr_is_okay:
                return_dict_detail[repo_name] = itr_dict_detail
            else:
                # If the upload is fail return immediately
                return_is_okay = itr_is_okay
                return_dict_detail[repo_name] = itr_dict_detail
                raise DebianError(
                    "Upload Failure at {deb}.\nDetails:{detail}"
                    .format(deb=repo_itr, detail=itr_dict_detail))
        result = RepositoryResult(return_is_okay, return_dict_detail)

        return result

class DebianErrorOnArtifactory(Exception):
    """
    Exception Class for raise when there is issue.
    """
    def __init__(self, msg):
        super(DebianError, self).__init__(self)
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

