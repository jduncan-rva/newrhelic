%{!?__python2: %global __python2 /usr/bin/python2}
%global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print (get_python_lib())")

Summary: RHEL/CentOS monitoring plugin for New Relic
Name: newrhelic
Version: 0.1
Release: 13%{?dist}
Source0: %{name}-%{version}.tar.gz
License: GPLv2
Group: Monitoring
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildRequires: python2-devel
BuildRequires: python-setuptools
BuildArch: noarch
Requires: python-daemon
Requires: python-psutil
%if ! (0%{?rhel} >= 7 || 0%{?fedora} >= 15)
Requires: chkconfig
Requires: initscripts
%else
%if 0%{?systemd_preun:1}
Requires(post): systemd-units
%endif
BuildRequires: systemd-units
%endif

Vendor: Jamie Duncan <jduncan@redhat.com>
Packager: Jamie Duncan <jduncan@redhat.com>
Url: https://github.com/jduncan-rva/newRHELic

%description
A Red Hat Enterprise Linux-specific monitoring plugin for New Relic.

%prep
%setup -q -n %{name}-%{version}

%build
%{__python2} setup.py build

%install
%{__python2} setup.py install -O1 --root=$RPM_BUILD_ROOT

%post
%if ! (0%{?rhel} >= 7 || 0%{?fedora} >= 15)
/bin/systemctl enable newrhelic.service
%else
/sbin/chkconfig --add newrhelic-plugin
%endif

%files
%config(noreplace) /etc/newrhelic.conf
%if ! (0%{?rhel} >= 7 || 0%{?fedora} >= 15)
%config %attr(0755, root, root) ${initddir}/newrhelic-plugin
%else
%{_unitdir}/newrhelic.service
%endif

%dir %{_docdir}/%{name}-%{version}
%{_docdir}/%{name}-%{version}/*
%{python2_sitelib}/*egg-info
%{python2_sitelib}/newrhelic*
%{_bindir}/newrhelic

%changelog
* Sun Feb 23 2014 Jamie Duncan <jduncan@redhat.com> 0.1-13
- improvements to spec file. looking to retire setup.cfg soon

* Sat Feb 14 2014 Jamie Duncan <jduncan@redhat.com> 0.1-12
- added spec file for future enhancement
- added socket timeout (hard-coded @ 5seconds) to try and fix
- the weird dead read syndrome we are seeing

* Sun Dec 15 2013 Jamie Duncan <jduncan@redhat.com> 0.1-10
- enabled an actual logging ability
- enabled better error handling for when data is slow to be retrieved

* Sun Nov 24 2013 Jamie Duncan <jduncan@redhat.com>
- made master version live in the config file
- moved pre/post install scripts into scripts directory

* Thu Nov 21 2013 Jamie Duncan <jduncan@redhat.com> 0.1-8
- made proxy type a config parameter

* Wed Nov 20 2013 Jamie Duncan <jduncan@redhat.com> 0.1-7
- urllib call wasn't routing through custom opener.
- fixed and tested on public https proxy

* Wed Nov 20 2013 Jamie Duncan <jduncan@redhat.com> 0.1-5
- fixed web proxy code to work (mostly stolen from @sschwartzman

* Tue Nov 19 2013 Jamie Duncan <jduncan@redhat.com> 0.1-4
- fixed leading slash to allow Sys Info to show up

* Thu Nov 14 2013 Jamie Duncan <jduncan@redhat.com> 0.1-3
- created setup.cfg to help with RPM creation

* Wed Nov 13 2013 Jamie Duncan <jduncan@redhat.com> 0.1-2
- continued work on packaging for CMS

* Wed Nov 13 2013 Jamie Duncan <jduncan@redhat.com> 0.1-1
- initial CMS-specific buildout
- added lockfile module
- altered default config file to disable NFS by default
