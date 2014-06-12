#!/usr/bin/env python

from distutils.core import setup, Extension
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read('conf/newrhelic.conf')

version = config.get('plugin','version')
name = 'newrhelic'

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
    data_files=[
        ('/etc',['conf/newrhelic.conf']),
        ('/usr/share/doc/%s-%s'% (name, version), ['doc/README','doc/LICENSE']),
        ('/etc/init.d', ['scripts/newrhelic-plugin']),
        ('/usr/lib/systemd/system', ['scripts/newrhelic.service']),
        ],
    )


