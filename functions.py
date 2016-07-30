#!/bin/python
import subprocess
import os

#RETURN 0 --> OK
#RETURN 1 --> CRITICAL

def check_yum_repo():
    #get system language
    #find for "enbled|habilitado" repositories
    lang=os.getenv('LANG')

    if "es_ES" in lang:
        command1="yum repolist all|grep -w habilitado|egrep -vi \"centos|epel\"|wc -l"
        value1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
        num1 = value1.communicate()[0].strip()
    elif "es_US" in lang:
        command1 = "yum repolist all|grep -w enabled|egrep -vi \"centos|epel\"|wc -l"
        value1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
        num1 = value1.communicate()[0].strip()
    else:
        print "System language not supported. [ES|EN]"
        return 1

    if num1 == "0":
        return 0
    else:
        return 1

def check_systemctl_enabled(service,status):
    #systemctl is-enabled service|grep -v status |wc -l == 0 --> OK
    command1="systemctl is-enabled "+service+"|grep "+status+" |wc -l"
    value1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
    num1 = value1.communicate()[0].strip()
    if num1 == "1":
        return 0
    else:
        return 1

def solve_systemctl_enabled(service,action):
    #systemctl action service
    command1 = "systemctl "+action+" "+service
    print command1
    value1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
    num1 = value1.communicate()[0].strip()
    if action == "disable":
        status="disabled"
    elif action == "enable":
        status="enabled"
    else:
        return 1

    res = check_systemctl_enabled(service,status)
    if res == 0:
        return 0
    else:
        return 1

def check_sticky():
    #df --local -P | awk {'if (NR!=1) print $6'} | xargs -I '{}' find '{}' -xdev -type d \( -perm -0002 -a ! -perm -1000 \)|wc -l
    #0 --> OK
    command1="df --local -P | awk {'if (NR!=1) print $6'} | xargs -I '{}' find '{}' -xdev -type d \( -perm -0002 -a ! -perm -1000 \)|wc -l"
    value1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
    num1 = value1.communicate()[0].strip()
    if num1 == "0":
        return 0
    else:
        return 1

def solve_sticky():
    #df --local -P | awk {'if (NR!=1) print $6'} | xargs -I '{}' find '{}' -xdev -type d -perm -0002 2>/dev/null | xargs chmod a+t
    command1="df --local -P | awk {'if (NR!=1) print $6'} | xargs -I '{}' find '{}' -xdev -type d -perm -0002 2>/dev/null | xargs chmod a+t"
    value1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
    num1 = value1.communicate()[0].strip()

    res = check_sticky()
    if res == 0:
        return 0
    else:
        return 1

def check_modprob(mod):
    #print "Check: " + mod
    #lsmod |grep cramfs|wc -l == 0 --> OK
    #modprobe -n -v cramfs|grep -v "install /bin/true"|wc -l == 0 --> OK

    command1="lsmod |grep "+mod+"|wc -l"
    command2="modprobe -n -v "+mod+"|grep -v \"install /bin/true\"|wc -l"

    value1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
    num1 = value1.communicate()[0].strip()

    value2 = subprocess.Popen(command2, stdout=subprocess.PIPE, shell=True)
    num2 = value2.communicate()[0].strip()

    if num1 == "0" and num2 == "0":
        return 0
    else:
        return 1

def solve_modprob(mod):
    #print "Solve: " + mod

    command1= "echo \"install "+mod+" /bin/true\">>/etc/modprobe.d/CIS.conf"

    value1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
    num1 = value1.communicate()[0].strip()

    res=check_modprob(mod)
    if res == 0:
        return 0
    else:
        return 1

def check_separate_partition(partition):
    #mount |grep -w "/tmp"|wc -l == 0 --> OK
    command1="mount |grep -w "+partition+"|wc -l"
    value1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
    num1 = value1.communicate()[0].strip()

    if num1 == 0:
        return 0
    else:
        return 1

def check_flag_partition(partition, flag):
    #mount |grep -w "/tmp"|grep -w "nodev"| wc -l
    command1="mount |grep -w "+partition+"|grep -w "+flag+"| wc -l"
    value1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
    num1 = value1.communicate()[0].strip()

    if num1 == 0:
        return 0
    else:
        return 1