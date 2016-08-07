#!/bin/python
import os, subprocess, yum, rpm, stat, re
from crontab import CronTab

#RETURN 0 --> OK
#RETURN 1 --> CRITICAL

def auth_single_mode():
    res1=grep_file(["/sbin/sulogin"], "/usr/lib/systemd/system/rescue.service")
    res2=grep_file(["/sbin/sulogin"], "/usr/lib/systemd/system/emergency.service")

    if res1 == 0 and res2 == 0:
        return 0
    else:
        return 1

def grep_file(strs,file):
    #Search if each str in strs, exist on file

    res = ["0"]*len(strs)

    f = open(file)

    for line in f:
        line = line.rstrip()
        pos = 0
        for st in strs:
            if re.search(st, line):
                res[pos]="1"
            pos=pos+1

    if "0" in res:
        return 1
    else:
        return 0

def solve_stat_file(file,gid,uid,perm):
    #Set perms, gui and uid to the file.
    os.chmod(file,perm)
    os.chown(file,uid,gid)

    res=check_stat_file(file,gid,uid,perm)
    if res == 0:
        return 0
    else:
        return 1

def check_stat_file(file,gid,uid,perm):
    #Check perms ex-->0644 , uid ex-->0 and gui ex-->0 of the file done, are same thats recibed
    fperm = oct(os.stat(file)[stat.ST_MODE])[-4:]
    fgid = oct(os.stat(file)[stat.ST_GID])
    fuid = oct(os.stat(file)[stat.ST_UID])

    if fgid == gid and fuid == uid and fperm == perm:
        return 0
    else:
        print "Critical PERMS: %s vs %s, UID: %s vs %s and GID: %s vs %s" % (fperm,perm,fuid,uid,fgid,gid)
        return 1


def add_cron(min,hour,command):

    tab = CronTab(user='root')
    cron_job = tab.new(command)
    cron_job.minute.on(min)
    cron_job.hour.on(hour)
    tab.write()

    res=check_cron(command)
    if res == 0:
        return 0
    else:
        return 1

def del_cron(command):

    cron_exist=check_cron(command)

    if cron_exist == 0:
        tab = CronTab(user='root')
        tab.remove_all(command)
        tab.write()
        res = check_cron(command)
    if res == 0:
        return 1
    else:
        return 0

def check_cron(command):
    num = 0

    tab = CronTab(user='root')
    cron_job = tab.find_command(command)

    for list in cron_job:
        num = num+1

    if num > 0:
        return 0

    return 1

def solve_rpm_installed(status,packages):
    #status 0 --> Remove packages if are installed.
    #status 1 --> Install packages if dont are installed.

    ts = rpm.TransactionSet()
    mi = ts.dbMatch()
    list = []
    for h in mi:
        list.append(h['name'])

    yb = yum.YumBase()

    if status == "1":
        for package in packages:
            if not yb.rpmdb.searchNevra(name=package):
                yb.install(name=package)
                yb.resolveDeps()
                yb.buildTransaction()

    if status == "0":
        for package in packages:
            if yb.rpmdb.searchNevra(name=package):
                yb.remove(name=package)
                yb.resolveDeps()
                yb.buildTransaction()

    yb.processTransaction()

    check=rpm_installed(status, packages)
    if check == 0:
        return 0
    else:
        return 1

def rpm_installed(status,packages):
    #status 0 --> Want packages not installed.
    #status 1 --> Want packages installed.

    #Add all packages to list
    ts = rpm.TransactionSet()
    mi = ts.dbMatch()
    list = []
    for h in mi:
        list.append(h['name'])

    for p in packages:
        if p in list:
            if status =="0":
                print "CRITICAL %s is installed." % (p)
                return 1
            if status =="1":
                print "OK %s is installed." % (p)
        else:
            if status == "0":
                print "OK %s NOT installed."% (p)
            if status == "1":
                print "CRITICAL %s is installed:" % (p)
                return 1

    return 0

def edit_file(path, cad_orig, cad_res):
    #Read all lines on file
    f = open(path, "r")
    lines = f.readlines()
    f.close()

    #If the beginning of line without blanks is cad_orig write cad_res else write normal line
    f = open(path, "w")
    for line in lines:
        if line.replace(" ","").startswith(cad_orig):
            f.write(cad_res+"\n")
        else:
            f.write(line)
    f.close()

def solve_gpg_activated():
    command1 = "grep -l \"^gpgcheck *=*.0\" /etc/yum.conf"
    value1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
    num1 = value1.communicate()[0].strip()
    if num1:
        edit_file("/etc/yum.conf","gpgcheck=0","gpgcheck=1")

    command2 = "grep -l \"^gpgcheck *=*.0\" /etc/yum.repos/*.repo"
    value2 = subprocess.Popen(command2, stdout=subprocess.PIPE, shell=True)
    num2 = value2.communicate()[0].strip()
    if num2:
        for value in num2.split():
            edit_file(value, "gpgcheck=0", "gpgcheck=1")

    check = gpg_activated()
    if check == 0:
        return 0
    else:
        return 1


def gpg_activated():
    #grep "^word1 *=*.word2"
    command1 = "grep \"^gpgcheck *=*.0\" /etc/yum.conf|wc -l"
    value1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
    num1 = value1.communicate()[0].strip()

    command2 = "grep \"^gpgcheck *=*.0\" /etc/yum.repos.d/*.repo|wc -l"
    value2 = subprocess.Popen(command2, stdout=subprocess.PIPE, shell=True)
    num2 = value2.communicate()[0].strip()

    if num1 == "0" and num2 == "0":
        return 0
    else:
        return 1

def solve_yum_gpg():
    #Delete repositories except epel or centos
    epel = "gpg-pubkey-352c64e5-52ae6884"
    centos = "gpg-pubkey-f4a80eb5-53a7ff4b"

    #Obtain list gpg repositories
    command1 = "rpm -q gpg-pubkey"
    value1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
    values = value1.communicate()[0].strip()

    #For each gpg if no centos or epel delete it
    for value in values.split():
        if value != epel and value != centos:
            command2="rpm -e "+value+" --allmatches"
            value2 = subprocess.Popen(command2, stdout=subprocess.PIPE, shell=True)
            res = value2.communicate()[0].strip()

    #Re-check
    check = check_yum_gpg()
    if check == 0:
        return 0
    else:
        return 1


def check_yum_gpg():
    epel="gpg-pubkey-352c64e5-52ae6884"
    centos="gpg-pubkey-f4a80eb5-53a7ff4b"

    command1="rpm -q gpg-pubkey |egrep -v \""+epel+"|"+centos+"\"|wc -l"
    value1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
    num1 = value1.communicate()[0].strip()

    if num1 == "0":
        return 0
    else:
        return 1


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

    if num1 == "0":
        return 0
    else:
        return 1

def check_flag_partition(partition, flag):
    #mount |grep -w "/tmp"|grep -w "nodev"| wc -l
    command1="mount |grep -w "+partition+"|grep -w "+flag+"| wc -l"
    value1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
    num1 = value1.communicate()[0].strip()

    if num1 == "0":
        return 0
    else:
        return 1