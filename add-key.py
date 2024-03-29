#!/usr/bin/env python

# add-key - Find or start an ssh-agent and then add an ssh key
#
# Copyright (C) 2017 Wolfgang Tichy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import print_function

import argparse
import subprocess
import os
import getpass
import glob

# use python's arg parser
parser = argparse.ArgumentParser(description=
    '''Find or start an ssh-agent and then add a ssh key. It works
       best together with eval.''',
    epilog='''Example:
    eval `add-key.py ~/.ssh/id_rsa_MK`''')
parser.add_argument('-t', metavar='LIFE', dest='life',
    help='lifetime of key in seconds, 0 means forever, default is 172800')
parser.add_argument('key', metavar='KEYFILE', nargs='?',
    help='name of ssh-key file, or -')

args = parser.parse_args()
if args.key == None:
    keyfile = ''
else:
    keyfile = args.key

# name of ssh-agent
sshagent = 'ssh-agent'

# find user name
#user = os.getlogin()
user = getpass.getuser()

# try to find first process that is ssh-agent
def find_sshagent(sshagent):
    # get all running processes
    out = subprocess.check_output(['ps', '-ef'])
    out = out.decode('latin_1') # convert to latin1 to avoid problems with MSB
    out = out.splitlines()      # convert to list of lines
    pid  = -1
    ppid = -1
    for line in out:
        linesplt = line.split()
        if linesplt[0] == user and (
           linesplt[7] == sshagent or linesplt[7] == '/usr/bin/'+sshagent ):
            pid = int(linesplt[1])
            ppid = int(linesplt[2])
            # print(line)
    return pid, ppid

# try to find ssh socket file
def find_ssh_auth_socket_file(pid, ppid):
    out = glob.glob('/tmp/ssh-*/agent.' + str(ppid))
    if len(out)==0:
        out = glob.glob('/tmp/ssh-*/agent.' + str(pid-1))
    if len(out)==0:
        out = glob.glob('/tmp/ssh-*/agent.*')
    if len(out)==0:
        return None
    else:
        return out[0]

# start a new sshagent
def start_new_sshagent(args):
    if args.life == None:
        os.system(sshagent + ' -t 172800')
    else:
        if args.life == '0' or args.life[0] == '-':
            os.system(sshagent)
        else:
            os.system(sshagent + ' -t ' + args.life)


# get pid
pid, ppid = find_sshagent(sshagent)

# if there is an agent, can we find its socket file?
if pid != -1:
    # check if SSH_AUTH_SOCK is set and if the file exists
    sock = os.environ.get('SSH_AUTH_SOCK')
    if sock == None:
        use_existing_sock = False
    else:
        use_existing_sock = True
        if not os.path.exists(sock):
            use_existing_sock = False
    if use_existing_sock == False:
        sock = find_ssh_auth_socket_file(pid, ppid)
    if sock == None:
        pid = -1 # signal that we need a new agent

# if there is no usable agent start a new one
if pid == -1:
    print('echo Started new', sshagent, ';')
    start_new_sshagent(args)
else:
    if use_existing_sock == True:
        print('echo Connecting to ssh-agent via existing SSH_AUTH_SOCK;')
        print('echo SSH_AUTH_SOCK=' + sock + ';')
    else:
        print('echo Connecting to ssh-agent with PID', pid, ';')
        com = 'SSH_AGENT_PID=' + str(pid) +'; export SSH_AGENT_PID;'
        print(com)
    com = 'SSH_AUTH_SOCK=' + sock +'; export SSH_AUTH_SOCK;'
    print(com)

# add key to sshagent
if keyfile != '-':
    com = 'ssh-add ' + keyfile + ';'
    print(com)
