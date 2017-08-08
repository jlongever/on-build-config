#!/bin/bash
set -x
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
if [ $? -eq 0 ] || [ -n ${RE_CONFIG_TAGS} ]; then
    # setup ansible env
    mv vmslave-config/pipeline/group_vars/* vmslave-config/ansible/group_vars
    hosts_file=`readlink -f hosts`
    export ANSIBLE_INVENTORY=$hosts_file
    cd vmslave-config/ansible
    if [ -n ${RE_CONFIG_TAGS} ]; then
        IFS=',' read -ra TAGS <<< "$RE_CONFIG_TAGS"
        for tag in "${TAGS[@]}"; do
            for book in `ls *.yml`; do
                # run target yml book
                cat $book | grep "hosts: ${tag}"
                if [ $? -eq 0 ]; then
                    ansible-playbook ${book}
                fi
            done
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
