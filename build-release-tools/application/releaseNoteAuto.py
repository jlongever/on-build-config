#!/usr/bin/env python
# Copyright 2015-2016, EMC, Inc.

"""
The script is used to automaticlly update the release notes page , add the new release information.

usage:
(1) prepare the config file  : releaseNotesConfig.conf

(2) run below command
./on-build-config/build-release-tools/HWIMO-BUILD on-build-config/build-release-tools/application/releaseNoteAuto.py
--release-version "1.2.3" \
--release-startDate "2017/02/03" \
--release-endDate "2017/02/10" \
--userName "$USER" \
--password "$PWD"

Options:
release-startDate : usually the sprint start date
release-endDate: usually the sprint end date
userName: the confluence user name
password:  the confluence user password


Requirements(python library dependency):
configparser				# to parse the config file
pyopenssl ndg-httpsclient pyasn1	# to depress the warning of "InsecurePlatformWarning: A true SSLContext object is not available"

"""

import argparse
from dateutil.parser import parse 
import traceback
import sys
import os
import requests
import json
import configparser
def release_note_args_parser(args):
    """
    This is a function to automatic generate the release notes on conflunence
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-version",
                          help = "This argument presents the version of release note",
                          action = "store")
                          
                          
    parser.add_argument("--release-startDate",
                          help = "This argument presents the start date of release note",
                          action = "store")
                          
                          
    parser.add_argument("--release-endDate",
                          help = "This argument presents the end date of release note",
                          action = "store")    
                          
    parser.add_argument("--userName",
                          help = "This argument presents conflunence user name",
                          action = "store")    

    parser.add_argument("--password",
                          help = "This argument presents conflunence password",
                          action = "store")                                  
    
    parsed_args = parser.parse_args(args)
    return parsed_args
    
def date_convert(args):
    """
    This is a function to convert date format to year-month-day
    """
    try:
         dt = parse(args)
         return dt.strftime('%Y-%m-%d')  
         
    except Exception, e:
    
        raise ValueError(e)
        
def get_page_content( url_base, page, space, user, pwd)    :
    """
    This is a function to get the data from a url
    """
    template_url = url_base +  "?title={0}&spaceKey={1}&expand=body.storage".format(page, space)
    response = requests.get(template_url,  auth=(user, pwd))
    if response.status_code != 200:
       raise RuntimeError("Fail to fetch content of confluence page " + page )
    data = response.json()
    return data

def get_page_change_version( url_base, page, space, user, pwd)    :
    """
    This is a function to get the page's latest version 
    """
    template_url = url_base + "?title={0}&spaceKey={1}&expand=version".format(page, space)
    response = requests.get(template_url,  auth=(user, pwd))
    if response.status_code != 200:
       raise RuntimeError("Fail to fetch change version of confluence page" + page)
    data = response.json()
    return data["results"][0]["version"]["number"]

def create_new_page( configs, user_name, passwd, start_date, end_date, version )   :
    """
    This is a function to create a new page for new release through post request to confluence 

    Jqurey for new features : ( (project=RAC and issuetype=Epic ) or (project = RI AND issuetype=Initiative ) ) AND status = Done AND "Affects Community" = Yes AND fixVersion = NA  ORDER BY priority DESC, key ASC, Rank ASC                

    Jqurey for fix bugs : project = RAC AND issuetype = Bug AND status = Done AND resolution in (Done) AND "Affects Community" = Yes AND   (  fixVersion = NA or (resolved >= 1900-01-01 AND resolved <= 2100-12-31))   ORDER BY cf[10506] ASC, priority DESC, key ASC, Rank ASC
   
    Jquery for open bugs : project = RAC AND issuetype = Bug AND status in ("To Do", "In Progress", Backlog) AND priority in (P1, P2, P3, "Not Set", "Needs Triage") AND "Affects Community" = Yes and status was NOT "Done" before "2100-12-31" ORDER BY key DESC      

    Jqurey for complete stories : project = RAC AND issuetype IN (Story) AND status = Done AND "Affects Community" = Yes AND  fixVersion = NA  AND resolution=Done ORDER BY priority DESC, key ASC, Rank ASC                                         
    """
    header = {'Content-type': 'application/json'}
    parent_page_name= configs["release_note_list_page"]
    parent_id = (get_page_content( configs["rest_url_base"], parent_page_name ,  configs["space_key"],  user_name, passwd))["results"][0]["id"]

    fix_version = "fixVersion = &quot;RackHD " + version+ "&quot;"
    data = get_page_content( configs["rest_url_base"], configs["template_page"], configs["space_key"], user_name, passwd )
    
    value = data["results"][0]["body"]["storage"]["value"]

    # replace the start date/end date and fix_version in the template
    value = value.replace( configs["template_start_date"], start_date)
    value = value.replace( configs["template_end_date"],end_date)    
    value = value.replace( configs["template_fix_version"],fix_version)    
    content = {"type":"page","title":"Release Notes " + version, "ancestors":[{"id": parent_id}], "space":{"key":configs["space_key"]},"body":{"storage":{"value": value,"representation":"storage"}}}
    post_response = requests.post(configs["rest_url_base"], headers = header, auth = (user_name , passwd), data = json.dumps(content))

    if post_response.status_code != 200:
       raise RuntimeError("Fail to post Confluence Restful API: create a new page. error: " + post_response.text )
 
def  update_release_page(configs, version, end_date, user_name, passwd)    :        
    """
    This is a function to update the table which present release infomation
    """
    
    header = {'Content-type': 'application/json'}
    new_row      = configs["template_new_row"]
    table_header = configs["template_header"]
    url_base     = configs["rest_url_base"]

    new_row = new_row.replace( configs["template_build_date"], end_date )
    new_row = new_row.replace( configs["template_version"], version )
    release_page_name=configs["overall_release_page"]
       
    change_version = get_page_change_version( url_base, release_page_name, configs["space_key"], user_name, passwd)
    data   = get_page_content( url_base, release_page_name, configs["space_key"], user_name, passwd )
    value  = data["results"][0]["body"]["storage"]["value"]
    page_id= data["results"][0]["id"]
    page_name=release_page_name.replace("+"," ")
    new_value = value.replace( table_header ,  table_header + new_row )
    #new_value  = new_value.replace("'","")
    update_page_url =  url_base  +  page_id
    content = { "id":page_id, "type":"page","title":page_name ,  "space":{"key":configs["space_key"]},"body":{"storage":{"value": new_value,"representation":"storage"}}, "version":{"number":str(change_version+1) }}

    put_response = requests.put(update_page_url, headers = header,auth = (user_name , passwd),data = json.dumps(content))

    if put_response.status_code != 200 :
       raise RuntimeError("Fail to put Confluence Restful Request: update release page :" + put_response.text )
    

def get_config_value( config_file ):
    """
    This is a function to get the key:values from a config file in .ini format
    """
    if os.path.isfile(config_file) == False:
       raise RuntimeError("Config File Not exist :" + config_file )

    configs = {} 
    cf = configparser.ConfigParser()
    cf.read(config_file)

    for section_name in cf.sections():
        for name, value in cf.items(section_name):
            configs[name] = value
            #print name, value
    return configs

####################################################################
def main():
    parsed_args= release_note_args_parser(sys.argv[1:])
    version    = parsed_args.release_version
    start_date = parsed_args.release_startDate
    end_date   = parsed_args.release_endDate
    user_name  = parsed_args.userName
    passwd     = parsed_args.password
    
    start_date = date_convert(start_date)
    end_date   = date_convert(end_date)

    try :
        dir_path = sys.path[0] 
        config_file = str(dir_path) + "/releaseNoteAuto.conf"
        configs = get_config_value(config_file)    
        create_new_page(configs, user_name, passwd, start_date, end_date, version)
        update_release_page(configs, version, end_date, user_name, passwd)
    except :
        traceback.print_exc()
        return 1


if __name__ == "__main__": 
    main() 
    
    
