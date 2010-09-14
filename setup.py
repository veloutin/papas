#!/usr/bin/env python
#
# Copyright 2008, Revolution Linux Inc.
#
# $Id$
#
# Author : Vincent Vinet <vvinet@revolutionlinux.com>
#
# -------------------------------------------------------------------------

import sys, os, shutil, getopt, re

from distutils.core import setup, Extension
from distutils.command import build_py

from django.core.management.commands import compilemessages

#init_dir = '/etc/init.d'
etc_dir = '/etc/apmanager' 
#lib_dir = '/var/lib'

data_files_list = [] 
#[(etc_dir, ['config/__init__.py', 'config/vsmanage_config.py'])]

def append_to_data_files(data_files_list, regexp, data_path, destination):
    for root, dirs, files in os.walk(data_path):
        # If the path does not contains ".svn"
        if root.find(".svn") == -1:
            # Keep only the files matching the regular expression
            file_list = filter(regexp.search, files)
            # Prepend the root path to each file in the list
            file_list = map((lambda file: os.path.join(root, file)), file_list)
            # Remove data_path from root
            root = root[len(data_path):]
            if len(root) >= 1 and root[0] == '/':
                root = root[1:]
            # Prepend the install path
            root = os.path.join(destination, root)
            # Associate this directory in the data_files_list
            data_files_list.append((root, file_list))

append_to_data_files(data_files_list, re.compile(r".*"), 'apmanager/templates', '/usr/share/papas/templates')
append_to_data_files(data_files_list, re.compile(r".*"), 'var/apmanager', '/var/lib/papas/')
append_to_data_files(data_files_list, re.compile(r".*"), 'etc', '/etc')
append_to_data_files(data_files_list, re.compile(r".*"), 'locale', '/usr/share/papas/locale')


# print '!!!', data_files_list


# packages_list = []
# #Need to include files in MANIFEST.in for this to work
# packages_data = {}
# for (dirpath, dirnames, filenames) in os.walk("vsmanage"):
#     if dirpath.find('.svn') != -1:
#         # skip .svn directories
#         continue
#     package_name = dirpath.replace('/', '.')
#     packages_list.append(package_name)
#      
#     packages_data[package_name] = ['*']

class CompileI18nBuildWrapper(build_py.build_py):
    def run(self):
        compilemessages.Command().execute()
        build_py.build_py.run(self)


setup(
    cmdclass={
        'build_py': CompileI18nBuildWrapper,
        },
    name="papas",
    version="0.9",
    description="simple django app to manage wifi hotspots",
    author="Revolution Linux",
    author_email="info@revolutionlinux.com",
    url="http://www.revolutionlinux.com",
    license="Proprietary",
    platforms=["Linux"],
    long_description="""Django Application To manage a group of Wifi Hotspots""",
    scripts=['bin/apmanager-cmdexecutor'],
    packages=[
        "apmanager",
        "apmanager.accesspoints",
        "apmanager.accesspoints.views",
        "apmanager.accesspoints.templatetags",
        "lib6ko",
        "lib6ko.protocols",
        "lib6ko.templatetags",
    ],
    #package_data=
    data_files = data_files_list,
)
