"""
This is a tool class holds the result of the iterating work of making
    debians and uploading the debians during Jenkins build process.
"""

import json

class RepositoryResult(object):
    """
    This is a tool class holds the result of the iterating work of making
    debians and uploading the debians during Jenkins build process.
    """
    def __init__(self, bool_is_good, dict_detail):
        """
        Initializer of this class
        :param bool_is_good: boolean whether this result means good or not.
        :param dict_detail: dictionary representation of all the repositories
        :return:
        """
        if type(bool_is_good).__name__ == "bool" \
                and type(dict_detail).__name__ == "dict":
            self.is_good = bool_is_good
            self.dict_detail = dict_detail
        else:
            raise ResultException(
                "Result need to be composed by a boolean value and dictionary "
                "detail")

    def __str__(self):
        """
        String representation of this result
        :return: str_detail
        """
        if self.is_good:
            return "Success"
        else:
            return "Fail"

    @staticmethod
    def str_detail(dict_res):
        """
        Static method to convert dictionary of detail result that used in
        DebianTools and build_artifacts to a human friendly result string.

        :param dict_detail: The 2 level result detail dictionary:
            {
            lev1_key : {
                lev2_key : status
                }
            }

            example:
                in blind_build_all():
                {
                'on-cli' : {
                    'HWIMO-TEST':'pass'/'fail'/'None',
                    'HWIMO-BUILD':'pass'/'fail'/'None'
                    }
                }

                in upload_debs():
                {
                'on-cli':{
                    'a.deb':'Success',
                    'b.deb':'Fail'
                    },
                'on-http': {}
                }

        :return: JSON string based representation of the dictionary
        """
        return json.dumps(dict_res, sort_keys=True, indent=4)

    def detail(self):
        return self.str_detail(self.dict_detail)

class ResultException(Exception):
    """
    Exception Class to raise when there is issue.
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

