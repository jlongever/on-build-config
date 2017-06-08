#!/usr/bin/env python
from mergefreezer import MergeFreezer
from argparse import ArgumentParser
import sys
import json

def parse_args(args):
    parser = ArgumentParser()
    parser.add_argument("--ghtoken",
                        help="Github token that have commit status set permission.",
                        required=True,
                        action="store")
    parser.add_argument("--manifest-file",
                        help="The file path of manifest which is the repo information source",
                        required=True,
                        action="store")
    parser.add_argument("--freeze-context",
                        help="The context of freeze pr commit status",
                        required=True,
                        action="store")
    parser.add_argument("--freeze-desc",
                        help="The description of freeze pr commit status",
                        required=True,
                        action="store")
    parser.add_argument("--unfreeze-desc",
                        help="The description of unfreeze pr commit status",
                        required=True,
                        action="store")
    parser.add_argument("--freeze",
                        help="The description of unfreeze pr commit status",
                        required=True,
                        action="store")

    parsed_args = parser.parse_args(args)
    return parsed_args

def main():
    parsed_args = parse_args(sys.argv[1:])
    with open(parsed_args.manifest_file) as manifest:
        manifest_dict = json.load(manifest)

    repo_list = []
    for repo_info in manifest_dict["repositories"]:
        repo_url = repo_info["repository"]
        repo_name = "/".join(repo_url[:-4].split("/")[-2:])
        repo_list.append(repo_name)

    mf = MergeFreezer(parsed_args.ghtoken, \
                      repo_list, \
                      parsed_args.freeze_context, \
                      parsed_args.freeze_desc, \
                      parsed_args.unfreeze_desc)

    if parsed_args.freeze.lower() == "true":
        mf.freeze_all_prs()
    elif parsed_args.freeze.lower() == "false" :
        mf.unfreeze_all_prs()
    else:
        print "Please make clear the action:\n    freeze: true\n    or\n    freeze false"

if __name__ == "__main__":
    main()
    sys.exit(0)