"""
    Dependencies:
        paramiko [$ pip install paramiko]
        GitPython [$ easy_install GitPython]
        A previous setup and configured docpage project - https://github.com/bevry/docpad
"""

import commands
import os
import time
import sys

import paramiko
from git import *

def getInfos(currentDir):
    infos = []
    for root, dirs, files in os.walk(currentDir): # Walk directory tree
        for f in files:
            infos.append(root + '/' + f)
    return infos

if __name__ == '__main__':

    repolocation = '../'
    buildpath = '../../../build/'
    remotepath = '/home/foote/webapps/gf_project_osa/'
    tries = 0
    repo = Repo(repolocation);

    localhead = repo.head
    remote = repo.remote()

    # Fetch remote.
    try:
        tries = tries+1
        remotehead = remote.fetch()
    except AssertionError:
        if tries <= 1:
            print 'Fetch error, trying again';
            remotehead = remote.fetch()
        else:
            print 'Try ' + tries + ' failed. Exiting.'
            exit()

    # Check for problems with fetch and compare remote head with local.
    if hasattr(remotehead[0], 'commit'):
        remotehead = remotehead[0]
        if remotehead.commit != localhead.commit:
            print 'Remote head commit (' + remotehead.commit.hexsha + ') does not match local (' + localhead.commit.hexsha + '). \nMerging!'
            info = remote.pull()
        else:
            print 'Nothing to update'
            exit()
    else:
        print 'Something went wrong'
        exit()

    # Use docpad to generate new HTML
    a = commands.getoutput('cd ' + buildpath + '; docpad clean; docpad generate');
    print a

    # Test connect to server
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkeylocation = os.path.expanduser('~/.ssh/id_dsa')
    key = paramiko.DSSKey.from_private_key_file(pkeylocation, 'eliza8bot')
    ssh.connect('foote.webfactional.com', username = 'foote', pkey = key)

    # Create sftp tansport
    transport = ssh.get_transport()
    sftp = paramiko.SFTPClient.from_transport(transport)

    # Traverse tree of files
    compiledpath = buildpath + 'out/'
    for f in getInfos(compiledpath):
        print 'Putting ' + f + ' to remote location ' + remotepath + f.replace(compiledpath, '')
        try:
            sftp.put(f, remotepath + f.replace(compiledpath, ''))
        except IOError as e:
            print 'Failed to put to :' + remotepath + f.replace(compiledpath, '') + "- [I/O error({0}): {1}".format(e.errno, e.strerror) + ']'

    sftp.close()
    ssh.close()
