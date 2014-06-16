#!/usr/bin/env python

from distutils.core import setup, Extension
import ConfigParser
import os

releaseFile = open('/etc/redhat-release','r')
distro_test = releaseFile.read()
d_version = distro_test[0].split()[0]
if d_version == 'Fedora':
    on_fedora = True
else:
    on_fedora = False

config = ConfigParser.RawConfigParser()
config.read('conf/newrhelic.conf')

version = config.get('plugin','version')
name = 'newrhelic'
data_files=[
    ('/etc',['conf/newrhelic.conf']),
    ('/usr/share/doc/%s-%s'% (name, version), ['doc/README','doc/LICENSE']),
]
if on_fedora:
    data_files.append(('/usr/lib/systemd/system', ['scripts/newrhelic.service']))
else:
    data_files.append(('/etc/rc.d/init.d', ['scripts/newrhelic-plugin']))
 
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
    py_modules=['newrhelic'],
    package_dir={'': 'src'},
    scripts = ['scripts/newrhelic'],
    data_files = data_files,
   )


