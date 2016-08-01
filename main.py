#!/usr/bin/env python

import os
from os import walk
from itertools import imap
import sys
import argparse
import re
import apt
import redis

# Check if sudo
if os.getuid() != 0:
    exit('You need to have root privileges to run thus script!')

# Create some important variables
unix_path = re.compile('^(/[^/ ]*)+/?$')
ip_address = re.compile('^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
redis_port = '6379'

# Get parameters
parser = argparse.ArgumentParser(description='Migrate PHP5 session to redis database.')
parser.add_argument('-d', '--dir', help='point PHP session directory', required=True, metavar='<dir>')
parser.add_argument('-r', '--redis', help='set redis server host (IP ONLY)', required=True, metavar='<ip>')
parser.add_argument('-p', '--port', help='change default (6379) redis port number', metavar='<port>')
parser.add_argument('-n', '--number', help='set proper redis database number', required=True, type=int, metavar='<id>')
args = parser.parse_args()

if unix_path.match(args.dir):
    session_dir = args.dir
else:
    print '\n[ERROR]: Please use valid path to PHP sessions directory. Use '+sys.argv[0]+' -h for help\n'
    sys.exit(1)

if ip_address.match(args.redis):
    redis_address = args.redis
else:
    print '\n[ERROR]: Please use valid format of IP address. Use '+sys.argv[0]+' -h for help\n'
    sys.exit(1)

if args.port != None:
    redis_port = args.port

database_number = args.number

# Check if php5-redis is installed
cache = apt.Cache()
pkg_name = 'php5-redis'

pkg = cache[pkg_name]
if cache[pkg_name].is_installed:
    print '[x] php5-redis package installed!'
else:
    cache.update()
    pkg.mark_install()

    try:
        cache.commit()
    except Exception, arg:
        print 'Can\'t found php5-redis package installed, do the installation right now... It could take a while.'
        print >> sys.stderr, 'Sorry, package installation failed [{err}]'.format(err=str(arg))

## Redis operando
# Get list of directories under session path:
dir_list = [ dirs for dirs in os.listdir(session_dir) if os.path.isdir(os.path.join(session_dir, dirs)) ]

f = []
r = redis.StrictRedis(host=redis_address, port=redis_port, db=database_number)
p = r.pipeline()
for (dirpath, dirnames, filenames) in walk(session_dir):
    f.extend(filenames)
    count_files = len(f)
    for counter in range(0, count_files):
        session_file = open(session_dir+'/'+f[counter])
        for line in session_file:
            print '[+] Migrate session: '+f[counter]+''
            p.set(f[counter], line.rstrip().split(' '))
p.execute()
