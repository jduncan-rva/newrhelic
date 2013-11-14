#!/usr/bin/env python

from distutils.core import setup, Extension

setup(name='NewRHELic',
    version='0.1',
    description='RHEL/CentOS monitoring plugin for New Relic',
    author='Jamie Duncan',
    author_email='jduncan@redhat.com',
    url='https://github.com/jduncan-rva/newRHELic',
    platform=['Linux'],
    maintainer='Jamie Duncan',
    maintainer_email = 'jduncan@redhat.com',
    long_description='A RHEL 6/CentOS 6-specific monitoring plugin for New Relic',
    packages=['psutil','daemon','daemon.version','lockfile'],
    py_modules=['newrelic'],
    ext_modules=[
        Extension('_psutil_linux',['psutil/_psutil_linux.c']),
        Extension('_psutil_posix',['psutil/_psutil_posix.c'])],
    scripts = ['newrhelic'],
    data_files=[
        ('/etc',['newrhelic.conf']),
        ('/usr/share/doc/NewRHELic-0.1', ['LICENSE', 'LICENSE-psutil', 'LICENSE-daemon', 'README', 'README.md']),
        ('/etc/init.d', ['newrhelic-plugin']),
        ],
    )


