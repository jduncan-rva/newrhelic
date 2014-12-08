%{!?__python2: %global __python2 /usr/bin/python2}
%global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print (get_python_lib())")

Summary: RHEL/CentOS monitoring plugin for New Relic
Name: newrhelic
Version: 0.2.0
Release: 14%{?dist}
Source0: %{name}-%{version}.tar.gz
#Source0: https://github.com/jduncan-rva/newRHELic/archive/%{name}-%{version}.tar.gz
#Source0: https://github.com/jduncan-rva/newRHELic/archive/%{release}.tar.gz
License: GPLv2
Group: Applications/System
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXXX)
BuildRequires: python2-devel
BuildRequires: python-setuptools
BuildArch: noarch
Requires: python
Requires: python-daemon
Requires: python-psutil
Requires(post): chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts
Obsoletes: NewRHELic 
Conflicts: NewRHELic
Vendor: Jamie Duncan <jduncan@redhat.com>
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
/sbin/chkconfig --add newrhelic-plugin

%preun
if [ $1 -eq 0]; then
    /sbin/service newrhelic-plugin stop >/dev/null 2>&1
    /sbin/chkconfig --del newrhelic-plugin
fi

%postun
if [ "$1" -ge "1" ]; then
    /sbin/service newrhelic-plugin condrestart >/dev/null 2>&1 || :
fi

%files
%config(noreplace) /etc/newrhelic.conf
%config %attr(0755, root, root) %{_initddir}/newrhelic-plugin
%dir %{_docdir}/%{name}-%{version}
%{_docdir}/%{name}-%{version}/*
%{python2_sitelib}/*egg-info
%{python2_sitelib}/newrhelic/*
%{_bindir}/newrhelic

%changelog
* Sun Nov 30 2014 Jamie Duncan <jduncan@redhat.com> 0.2.0-9
- caught unhandled ssl read error - fixes #25

* Sat Nov 29 2014 Jamie Duncan <jduncan@redhat.com> 0.2.0-8
- refactored CPU Percent States for versions of psutil that do not have that function. fixes #24

* Thu Nov 27 2014 Jamie Duncan <jduncan@redhat.com> 0.2.0-2
- fixed typo in cpu states function

* Wed Nov 26 2014 Jamie Duncan <jduncan@redhat.com> 0.2.0-1
- a little clean up and getting ready for 0.2
- starting to get spec file ready for fedora in case we want to submit

* Thu Jun 12 2014 Tommy McNeely <tommy@lark-it.com> 0.1-16
- Added Obsoletes / Conflicts to replace old name

* Thu Jun 12 2014 Tommy McNeely <tommy@lark-it.com> 0.1-15
- Fixing all the EL7 vs EL6 vs EL5 issues (EL7 stuff was added by jduncan)

* Thu Jun 12 2014 Tommy McNeely <tommy@lark-it.com> 0.1-14
- attempts at making the same spec file work for EL5 and EL6

* Sun Feb 23 2014 Jamie Duncan <jduncan@redhat.com> 0.1-13
- improvements to spec file. looking to retire setup.cfg soon

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
