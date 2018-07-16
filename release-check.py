#!/usr/bin/env python3

import os
import sys
import urllib.request
import subprocess
from subprocess import run
import tarfile
import tempfile
import argparse

import getpass
from github3 import login

parser = argparse.ArgumentParser(prog='cfitsio_notify')
parser.add_argument('-p',
        '--prompt',
        action='store_true',
        help='Prompt for interactive password entry. Overrides default behavior'
        ' of accepting the password to use via the environment variable'
        ' CFITSIO_NOTIFY_PW.')
parser.add_argument('-t',
        '--testing',
        action='store_true',
        help='All output to local console. Does not communicate with Github.')
parser.add_argument('username',
        type=str,
        help='Required. Github username to use when authenticating for API use.')
parser.add_argument('full_repo',
        type=str,
        help='Required. Repository in which an issue comment should be posted.'
             'Specified in the form <organization>/<repository>')
parser.add_argument('issue',
        type=str,
        help='The pre-existing issue number to which release notification '
             'should be posted.')

args = parser.parse_args()

if not args.testing:
    if args.prompt:
        password = getpass.getpass()
    else:
        try:
            password = os.environ['RELEASECHECK_PW']
        except KeyError:
            print('Environment variable RELEASECHECK_PW not defined.')
            print('Store the Github password in that variable or run with `-p` to'
                    'prompt for the password interactively.')
            sys.exit(1)


# A priori: compute MD5 of cfitsio 3.45, store persistently on disk.
# Get latest tarball
# Compute MD5 of tarball
# Compare hash to previously stored value (kept in some persistent
#   filesystem storage area.)
# If the hash are identical, exit.
# If the hashes differ, unpack the tarball and extract the SONAME value
#  compare SONAME value with previously stored value (kept in same
#   persistent storage area.)
#   Also extract latest changelog section for inclusion in github issue text.
#   Indicate that a new release has been made in Github issue comment.
# If the SONAME value differs, also indicate this in the status message.


latest_tar = 'cfitsio_latest.tar.gz'
latest_URL = 'http://heasarc.gsfc.nasa.gov/FTP/software/fitsio/c/{}'.format(latest_tar)
reference_file = './cfitsio_reference'
fitsio_h = 'cfitsio/fitsio.h'
changesfile = 'cfitsio/docs/changes.txt'


def compute_md5(fname):
    import hashlib
    md5 = hashlib.md5()
    BUF_SIZE = 65536

    with open(fname, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
    return(md5.hexdigest())

# Get the latest tarball, and examine it for version information.
# Compare this with the cached reference version info and if the latest
# tarball is different from the reference, post a notification to Github
# explaining this, with an excerpt of the tarball's changelog.
with tempfile.TemporaryDirectory() as tmpdir:

    print('Reading cfitsio version reference info from: {}'.format(reference_file))
    with open(reference_file) as f:
        refvals = f.read().strip().split()
        ref_md5 = refvals[0]
        ref_ver = refvals[1]
        ref_soname = refvals[2]
    print('reference version {}'.format(ref_ver))
    print('reference SONAME  {}'.format(ref_soname))

    os.chdir(tmpdir)
    urllib.request.urlretrieve(latest_URL, latest_tar)
    md5 = compute_md5(latest_tar)

    if ref_md5 == md5:
        print('Latest tarball hash is the same as reference.')
    else:
        print('Latest tarball hash does not match reference. Unpacking new version.')
        tfile = tarfile.open(latest_tar, mode='r')
        tfile.extract(fitsio_h)
        tfile.extract(changesfile)
        ef = open(fitsio_h)
        lines = ef.readlines()

        # Extract version and SONAME values from the source code.
        for line in lines:
            if 'CFITSIO_VERSION' in line.strip():
                version = line.strip().split()[2]
                print('New version       {}'.format(version))
                break
        for line in lines:
            if 'CFITSIO_SONAME' in line.strip():
                soname = line.strip().split()[2]
                print('New SONAME        {}'.format(soname))
                break

        # Get changelog message for the latest release.
        comment = ('This is a message from an automated system that monitors `cfitsio` releases.\n'
                  '`cfitsio`')
        with open(changesfile) as cf:
            sec_open = False
            for line in cf.readlines():
                if 'Version' in line.strip() and sec_open:
                    break
                if 'Version' in line.strip() and not sec_open:
                    sec_open = True
                    comment += line
                    continue
                if sec_open:
                    comment += line
                    continue
        if ref_soname != soname:
            comment += '\n**NOTE: This release introduces a SONAME change from {} to {}.**'.format(
                ref_soname, soname)

        # Push changes text to a new/existing issue on Github.
        if args.testing:
            print(comment)
        else:
            print('Posting comment to Github...')
            gh = login(args.username, password=password)
            #issue = gh.issue(args.username, 'auto-test', '1') 
            repo = args.full_repo.split('/')
            issue = gh.issue(repo[0], repo[1], args.issue) 
            issue.create_comment(comment)

        # Update version reference to inform the next run.
        os.chdir(sys.path[0])
        reference = '{} {} {}'.format(md5, version, soname)
        print(reference)
        print('Updating cfitsio version refrence.  ',end='')
        try:
            with open(reference_file, 'w') as f:
                f.write(reference)
            print('Done.')
        except:
            print('\nERROR writing reference file. To provide the correct reference\n'
                'for the next run and avoid duplicated Github issue comments, \n'
                'copy the following line as the sole contents the file \n'
                '{}.\n\n'
                '{}'.format(reference_file, reference))

