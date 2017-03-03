# Introduction

This is an ansible playbook to config vmslave of jenkins for CI.

# Example Usage: Config PR Gate vmlaves

1. Create a group ```prgate``` in your ansible/hosts. ```ip, ansible_user, ansible_ssh_pass, ansible_become_pass(sudo pass)``` are needed for each host item.
2. Full fill the necessary vars in ```group_vars/all && group_vars/prgate```.
3. Run ```ansible-playbook pr_gate_vmslave_config.yml```, this will configurate every host in prgate group to the prod conditon.

You can edit ```pr_gate_vmslave_config.yml``` to filter roles you wanted.
If you want to expand this playbook, http://docs.ansible.com/ansible/playbooks_best_practices.html is suggested.
