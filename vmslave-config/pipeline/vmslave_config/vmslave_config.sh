#!/bin/bash

which shyaml
if [ $? -ne 0 ]; then
    echo "Missing package: shyaml. Please pip install shyaml"
    exit 1
fi

#list diff files
diff_files=`git diff --dirstat=files ${GIT_PREVIOUS_COMMIT}`
echo $diff_files | grep "vmslave-config/"

# one yml for one group
# RE_CONFIG=true config all groups, else config changed group
if [ $? -eq 0 ] || [ ${RE_CONFIG} == "true" ]; then
    # setup ansible env
    mv vmslave-config/pipeline/group_vars/* vmslave-config/ansible/group_vars
    hosts_file=`readlink -f hosts`
    export ANSIBLE_INVENTORY=$hosts_file
    cd vmslave-config/ansible
    if [ ${RE_CONFIG} == "true" ]; then
        # run all yml book
        for book in `ls *.yml`; do
            ansible-playbook ${book}
        done
    else
        for book in `ls *.yml`; do
            roles=`cat $book | shyaml get-values | shyaml get-value roles | shyaml get-values`
            for role in roles; do
                # find changed roles and re-config relevant group
                echo $diff_files | grep $role
                if [ $? -eq 0 ]; then
                    ansible-playbook ${book}
                    break
                fi
                echo $diff_files | grep $book
                if [ $? -eq 0 ]; then
                    ansible-playbook ${book}
                    break
                fi
            done
        done
    fi
fi
