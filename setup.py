#!/usr/bin/env python

from distutils.core import setup, Extension
import ConfigParser
import os

exec(open('src/_version.py').read())
name = 'newrhelic'
version = __version__
data_files=[
    ('/etc',['conf/newrhelic.conf']),
    ('/usr/share/doc/%s-%s'% (name, version), ['doc/README','doc/LICENSE']),
    ('/etc/rc.d/init.d', ['scripts/newrhelic-plugin'])
]
 
setup(
    name=name,
    version=version,
    description='RHEL/CentOS monitoring plugin for New Relic',
    author='Jamie Duncan',
    author_email='jduncan@redhat.com',
    url='https://github.com/jduncan-rva/newRHELic',
    maintainer='Jamie Duncan',
    maintainer_email = 'jduncan@redhat.com',
    long_description='A RHEL 6/CentOS 6-specific monitoring plugin for New Relic (http://www.newrelic.com)',
    packages=['newrhelic'],
    package_dir={'newrhelic': 'src'},
    scripts = ['scripts/newrhelic'],
    data_files = data_files,
   )
