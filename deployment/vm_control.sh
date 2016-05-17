#!/bin/bash
operation_file="vm_operation.sh"
Usage()
{
    echo "Function: this script is used to power_on/power_off/delete VMs"
    echo "Usage: OPTION SERVER_INFO [SERVER_INFO]"
    echo "  OPTION:"
    echo "    -h: give this help list"
    echo "    -f: Obtain SERVER_INFO from FILE, one per line.  The empty file contains zero INFO, and therefore matches nothing."
    #echo "    -a: the aciton should be taken on the specific VM. \"power_on\",\"power_off\" and \"delete\" are supported"
    echo "  SERVER_INFO: \"ip,user_name,password,action,duration,vm_name[,vm_name]\" "
    echo "    ip       : the IP address of ESXi server"
    echo "    user_name: the user name of ESXi server"
    echo "    password : the password of ESXi server."
    echo "    action   : the action should be taken on the specific VM. power_on,power_off and delete are supported"
    echo "    duration :the duration time between the action, the unit is second(s)"
    echo "    vm_name  : the name of VM which will be operated. Regular Expression is supported"
}

shift_num=0
arg_type="command"
arg=""

configure_handle() #handle the configure file
{
    while read line
    do
        echo $line | grep "^#" > /dev/null  2>&1
        if [ $? -eq 0 ];then continue;fi #parse the comments which starts with "#"
        server_info=`echo $line | sed /^[[:space:]]*$/d | awk -F '=' '{print $2}' | sed 's/[[:space:]]//g'`
        arg=$arg$server_info" "
    done<$1
}

OLD_IFS=$IFS
to_array() #transform input to a array using the given IFS
{
    IFS=$2
    result=($1)
    i=0
    result_num=${#result[@]}
    while [ $i -lt $result_num ]
    do
        if [ -z ${result[$i]} ];  then #replace null with "null"
            result[$i]="null"
        fi
        let i++
    done
    echo ${result[@]}
    return 0
}

ip_check() #check the input if a valid ip address
{
    echo $1
    echo $1|grep "^\([0-9]\{1,3\}\.\)\{3\}[0-9]\{1,3\}$" > /dev/null #should be xxx.xxx.xxx.xxx
    if [ $? -ne 0 ]; then
        echo "ERROR: the IP format should be xxx.xxx.xxx.xxx"
        return 1
    fi
    ip=(`to_array $1 "."`)
    if [ ${ip[0]} -gt 255  -o  ${ip[1]} -gt 255  -o  ${ip[2]} -gt 255  -o  ${ip[3]} -gt 255 ]; then #number should be less than 255
        echo "ERROR: the content of each IP field should be less than 255"
        return 1
    fi
    return 0
}
number_check() #check the input if a number
{
    tmp=`echo $1 |sed 's/[0-9]//g'`
    if [ -n "${tmp}" ]; then
        echo "ERROR: $2 should be number"
        return 1
    else
        return 0
    fi
}

while getopts "f:h" optname
do
    case "$optname" in
        "f")arg_type="configure"
            configure_file=$OPTARG
            if [ -f $configure_file ];then
                configure_handle $configure_file
            else
                echo "ERROR: there is no configure file"
                exit 1
            fi
            ;;
        "h")Usage;exit 1;;
        "?")echo "invalid argument"
            Usage
            exit 1
            ;;
    esac
done

#check the necessary pacakge
which expect > /dev/null 2>&1
if [ $? -ne 0 ] ; then
    echo "expect package is not installed, please use the command to isntall:"
    echo "sudo apt-get install expect"
    exit 1
fi

shift $shift_num #remove the option to make the node information as the first argument

if [ $# -eq 0 ]; then
    echo "ERROR: there is no server information, could't operate VM"
    exit 1
fi
if [ $arg_type = "command" ];then
    echo "deploy VM(s) using command argument"
    arg="$@"
else
    echo "deploy VM(s) using configure file"
fi

for node in $arg
do
    node=`echo $node | sed "s/[\"\']//g"`
    node_info=(`to_array $node ","`)
    arg_num=${#node_info[@]}
    if [ $arg_num -lt 6 ];then
        echo "ERROR: the number of argument for node $node should not less than 6(ip,user_name,password,action,duration,vm_name[,vm_name])"
    fi
    arg_pos=0
    while [ $arg_pos -lt $arg_num ]
    do
        arg_contents=`echo ${node_info[$arg_pos]} | awk '{sub(/^ */,"");sub(/ *$/,"")} $0'` #slip ' '
        node_info[$arg_pos]=$arg_contents
        let arg_pos++
    done
    if [ -z ${node_info[0]} ]; then
        echo "ERROR: the IP address of node '$node' is NULL"
        continue
    else
        server_ip=${node_info[0]}
        ip_check $server_ip
        if [ $? -ne 0 ]; then continue; fi
    fi
    if [ "${node_info[1]}" = "null" ]; then
        echo "ERROR: The user_name of node '$node' is NULL"
        continue
    else
        server_user_name=${node_info[1]}
    fi
    if [ "${node_info[2]}" = "null" ]; then
        echo "ERROR: The PASSWORD of node '$node' is NULL"
        continue
    else
        server_password=${node_info[2]}
    fi
    ./scp_transfer.exp $server_ip $server_user_name $server_password $operation_file
    ./check_scp.exp $server_ip $server_user_name $server_password $operation_file > /dev/null 2>&1
    if [ $? -ne 0 ];then
        echo "ERROR: file $operation_file scp fails"
        continue
    fi
    echo "power_on power_off delete" | grep -w ${node_info[3]} > /dev/null 2>&1
    if [ $? -ne 0 ];then
        echo "ERROR: value of action ${node_info[3]} is not expected"
        continue
    else
        vm_action=${node_info[3]}
    fi
    duration=${node_info[4]}
    number_check $duration "duration time between operation of VMs"
    if [ $? -ne 0 ];then
        echo "set the duration as the default value 0"
        duration=0
    fi
    arg_pos=5
    while [ $arg_pos -lt $arg_num ]
    do
        vm_name=${node_info[$arg_pos]}
        let arg_pos++
        ./ssh_login.exp $server_ip $server_user_name $server_password /$operation_file $vm_action $duration $vm_name
    done
done
