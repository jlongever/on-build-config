#!/usr/bin/env python

###########################
# parse the test result to get the count of failed cases, total cases, skipped cases
###########################

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import sys
import os
import argparse

def parse_args(args):
    """
    Parse script arguments.
    :return: Parsed args for assignment
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--test-result-files',
                        required=True,
                        help="The file path of test result",
                        action='store')

    parser.add_argument('--parameters-file',
                        help="The jenkins parameter file that will used for succeeding Jenkins job",
                        action='store',
                        default="downstream_parameters")

    parsed_args = parser.parse_args(args)
    return parsed_args

def get_value(root, key):
    value = 0
    if key in root.attrib:
        value = int(root.get(key))
    return value

def get_summary(root, summary):
    for key in ["tests", "errors", "failures", "skip", "skipped"]:
        summary[key] += get_value(root, key)
    return summary

def write_parameters(filename, params):
    """
    Add/append parameters(java variable value pair) to the given parameter file.
    If the file does not exist, then create the file.
    :param filename: The path of the parameter file
    :param params: the parameters dictionary
    :return:None on success
            Raise any error if there is any
    """
    if filename is None:
        raise ValueError("parameter file name is not None")
    with open(filename, 'w') as fp:
        for key in params:
            entry = "{key}={value}\n".format(key=key, value=params[key])
            fp.write(entry)


def main():
    args = parse_args(sys.argv[1:])
    test_result_files = args.test_result_files.split(' ')
    summary = {}
    summary["tests"] = 0
    summary["errors"] = 0
    summary["failures"] = 0
    summary["skip"] = 0
    summary["skipped"] = 0
    summary["time"] = 0
    for result_file in test_result_files:
        root = ET.parse(result_file).getroot()
        summary = get_summary(root, summary)
        
    write_parameters(args.parameters_file, summary)

if __name__ == '__main__':
    main()
