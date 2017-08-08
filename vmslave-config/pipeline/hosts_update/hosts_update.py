#!/usr/bin/env python

import sys
import jenkins
import xml.etree.ElementTree as ET
import argparse

class JenkinsSlaveHostsGenerator():

    def __init__(self, url, user, password, output, extra_text):
        self.jenkins = jenkins.Jenkins(url, username=user, password=password)
        self.output_path = output
        self.extra_text = extra_text

    def generate_hosts_file(self):
        """
        main method
        """
        nodes_map = self.generate_nodes_map()
        self.write_hosts_file(nodes_map)

    def generate_nodes_map(self):
        """
        nodes_map: {"label":[(host_name, host_ip), ......]}
        """
        nodes_map = dict()
        all_nodes = self.jenkins.get_nodes()
        for node in all_nodes:
            if node['name'] == "master":
                continue

            # parse node config xml
            node_config_xml = self.jenkins.get_node_config(node["name"])
            node_xml_root = ET.fromstring(node_config_xml)
            label_str = node_xml_root.find('label').text
            if not label_str:
                continue

            # add label and hosts to dict
            label_list = label_str.split()
            ip = node_xml_root.find("launcher").find("host").text
            host = (node["name"], ip)
            for label in label_list:
                if nodes_map.has_key(label):
                    nodes_map[label].append(host)
                else:
                    nodes_map[label] = [host]
        return nodes_map

    def write_hosts_file(self, nodes_map):
        """
        generate hosts file
        """
        hosts_text = ""
        for label, hosts_list in nodes_map.iteritems():
            # hosts group tag
            hosts_text += "[{0}]\n".format(label)
            for host in hosts_list:
                # hosts items
                hosts_text += "{0} ansible_host={1} {2}\n".format(host[0].replace(" ",""), host[1], self.extra_text)
            # end a group(label)
            hosts_text += "\n"

        with file(self.output_path, 'w') as f:
            f.write(hosts_text)


def parse_args(args):
    """
    Parse script arguments.
    :return: Parsed args for assignment
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('--jenkins-url',
                        required=True,
                        help="jenkins host url",
                        action='store')

    parser.add_argument('--jenkins-user',
                        required=True,
                        help="jenkins admin user name",
                        action='store')

    parser.add_argument('--jenkins-pass',
                        required=True,
                        help="jenkins admin password",
                        action='store')

    parser.add_argument('--extra-text',
                        required=True,
                        help="except host ip, extra text in ansible hosts item",
                        action='store')

    parser.add_argument('--output-path',
                        required=True,
                        help="hosts file outpath path",
                        action='store')


    parsed_args = parser.parse_args(args)
    return parsed_args

def main():
    """
    Generate a host file contains all jenkins nodes, group_name==node_label
    """

    args = parse_args(sys.argv[1:])
    generator = JenkinsSlaveHostsGenerator(args.jenkins_url, args.jenkins_user, args.jenkins_pass, args.output_path, args.extra_text)
    generator.generate_hosts_file()


if __name__ == '__main__':
    main()
