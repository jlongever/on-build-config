#!/usr/bin/env python
from argparse import ArgumentParser
import jenkins
import sys

def gain_job_control(job_name, sentry, force):
    job = server.get_job_info(job_name)

    for build_index in job["builds"][1:]:
        build = server.get_build_info(job_name, build_index['number'])

        if not build["building"]:
            continue

        if force.lower() == "true":
            server.stop_build(job_name, build_index['number'])
        else:
            for para in build['actions'][0]['parameters']:
                if para["name"] != sentry:
                    continue
                if para["value"].lower() == "true":
                    print "A build of high priority is running, can't stop it."
                    sys.exit(1)
                else:
                    server.stop_build(job_name, build_index['number'])

def parse_args(args):
    parser = ArgumentParser()
    parser.add_argument("--jenkins-cred",
                        help="Jenkins cred that have admin permission.",
                        required=True,
                        action="store")
    parser.add_argument("--jenkins-url",
                        help="Target Jenkins url.",
                        required=True,
                        action="store")
    parser.add_argument("--force",
                        help="Force grab the job control without check sentry var",
                        required=True,
                        default=False,
                        action="store")
    parser.add_argument("--sentry",
                        help="Point out the sentry var name, if sentry=true, do nothing else grab the job control",
                        required=True,
                        action="store")
    parser.add_argument("--job-name",
                        help="The target job name",
                        required=True,
                        action="store")


    parsed_args = parser.parse_args(args)
    return parsed_args

def main():
    parsed_args = parse_args(sys.argv[1:])
    user, password = parsed_args.jenkins_cred.split(":")
    global server
    server = jenkins.Jenkins(parsed_args.jenkins_url, \
                                   username=user, \
                                   password=password)
    gain_job_control(job_name=parsed_args.job_name,\
                     sentry=parsed_args.sentry, \
                     force=parsed_args.force)

if __name__ == "__main__":
    main()
    sys.exit(0)
