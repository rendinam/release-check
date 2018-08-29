#!/usr/bin/env python3

import os
import sys
import configparser
import urllib.request
import subprocess
from subprocess import run
import tarfile
import tempfile
import argparse
import shutil
from contextlib import contextmanager

import yaml
import getpass
import github3

parser = argparse.ArgumentParser(prog='release-check')
parser.add_argument('-p',
        '--password',
        action='store_true',
        help='Prompt for interactive password entry. Overrides default behavior'
        ' of accepting the password to use via the environment variable'
        ' RELEASECHECK_PW.')
parser.add_argument('-d',
        '--dry-run',
        action='store_true',
        help='All output to local console. Does not communicate with Github.')
parser.add_argument('username',
        type=str,
        help='Github username to use when authenticating for API use.'
        'Required if -t not used.')
parser.add_argument('-r',
        '--refdir',
        type=str,
        help='Directory where program will check for the reference version file.'
        ' When the flag is not used, the default is the current working directory.')
parser.add_argument('notify_repo',
        type=str,
        help='Required. Repository in which an issue comment should be posted.'
        'Specified in the form <organization>/<repository>')
parser.add_argument('-c',
        '--config',
        type=str,
        help='Required. Configuration file defining dependencies to query.')

args = parser.parse_args()

if not args.config:
    print('Please supply a config file name as an argument.')
    sys.exit(1)

if not args.dry_run:
    if args.password:
        password = getpass.getpass()
    else:
        try:
            password = os.environ['RELEASECHECK_PW']
        except KeyError:
            print('Environment variable RELEASECHECK_PW not defined.')
            print('Store the Github password in that variable or run with `-p` to'
                    'prompt for the password interactively.')
            sys.exit(1)

if not args.refdir:
    refdir = './'
else:
    refdir = args.refdir

config = configparser.ConfigParser()
config.read(args.config)
depnames = config.sections()
print(depnames)
import importlib




@contextmanager
def pushd(newDir):
    '''Context manager function for shell-like pushd functionality

    Allows for constructs like:
    with pushd(directory):
        'code'...
    When 'code' is finished, the working directory is restored to what it
    was when pushd was invoked.'''
    previousDir = os.getcwd()
    os.chdir(newDir)
    yield
    os.chdir(previousDir)


class release_notifier():

    def __init__(self, depname):
        self.dep_name = depname
        self.ref_file = os.path.join(refdir, '{}_reference'.format(self.dep_name))
        with open(self.ref_file) as f:
            self.ref_ver_data = yaml.safe_load(f)
        self.new_ver_data = None
        self.md5 = None
        self.ref_md5 = None
        self.issue_title_base = 'Upstream release of dependency: '
        self.issue_title = self.issue_title_base + self.dep_name
        self.comment_base = ('This is a message from an automated system '
            'that monitors `{}` releases.\n'.format(self.dep_name))
        self.dry_run = False
        self.remote_ver = None

    def get_version(self):
        return depchecker.get_version()

    def get_changelog(self, ref_ver_data, new_ver_data):
        return depchecker.get_changelog(ref_ver_data, new_ver_data)

    def new_version(self):
        print('Reading version reference info from: {}'.format(self.ref_file))
        with open(self.ref_file) as f:
            ver_info = yaml.safe_load(f)
        if self.remote_ver != ver_info['version']:
            return True
        else:
            return False

    def create_github_issue(self):
        # Push changes text to a new/existing issue on Github.
        self.comment = self.comment_base + '/n' + self.comment
        if self.dry_run:
            print(self.comment)
        else:
            print('Posting comment to Github...')
            gh = github3.login(args.username, password=password)
            repo = args.notify_repo.split('/')
            gh.create_issue(repo[0], repo[1], self.issue_title, self.comment)

    def update_version_ref(self):
        # Update version reference to inform the next run.
        os.chdir(sys.path[0])
        print('Backing up old version reference...')
        self.ref_backup = self.ref_file + '.bkup'
        shutil.copy(self.ref_file, self.ref_backup)

        print('Updating {} version refrence.  '.format(self.dep_name), end='')
        try:
            with open(self.ref_file, 'w') as f:
                reference = yaml.safe_dump(self.new_ver_data)
                print(reference)
                f.write(reference)
            print('Done.')
        except:
            print('\nERROR writing reference file. To provide the correct reference\n'
                'for the next run and avoid duplicated Github issue comments, \n'
                'copy the following line as the sole contents the file \n'
                '{}.\n\n'
                '{}'.format(self.ref_file, reference))

    def post_notification(self):
        self.update_version_ref()
        # For each notification type desired, post one.
        # TODO: support notification types:
        #       e-mail?
        #       confluence?
        #       slack?
        try:
            self.create_github_issue()
        except:
            # roll back version reference
            shutilcopy(self.ref_backup, self.ref_file)

    def check_for_release(self):
        with tempfile.TemporaryDirectory() as self.tmpdir:
            with pushd(self.tmpdir):
                self.new_ver_data = self.get_version()
                self.remote_ver = self.new_ver_data['version']
            if n.new_version():
                with pushd(self.tmpdir):
                    self.comment = self.get_changelog(self.ref_ver_data, self.new_ver_data)
                    self.post_notification()
            else:
                print('No new version detected for {}.'.format(self.dep_name))


# For each dependency defined in the config file, query it for new releases
# and post a notification if one is found.
for depname in depnames:
    plugin = config[depname]['plugin'].strip()
    print('Plugin = {}'.format(plugin))
    try:
        depchecker = importlib.import_module(plugin)
    except:
        print('Import of plugin for {} failed.'.format(depname))
    n = release_notifier(depname)
    n.check_for_release()
