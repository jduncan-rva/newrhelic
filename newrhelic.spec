
# EL5 will require python26 from EPEL
%if 0%{rhel} == 5
%global pyver 26
%global pybasever 2.6
%global __os_install_post %{__python26_os_install_post}
%else
%global pyver 2
%global pybasever 2.6
%endif

# Not sure about others

%global __python %{_bindir}/python%{pybasever}

%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name: newrhelic
Version: 0.1
Release: 14%{?dist}
Summary: RHEL/CentOS monitoring plugin for New Relic

Group: Applications/System
Vendor: Jamie Duncan <jduncan@redhat.com>
License: GPLv2
URL: https://github.com/jduncan-rva/newRHELic
Source0: %{name}-%{version}.tar.gz
#Source0: https://github.com/jduncan-rva/newRHELic/archive/%{name}-%{version}.tar.gz
#Source0: https://github.com/jduncan-rva/newRHELic/archive/%{release}.tar.gz
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXXX)

BuildArch: noarch
BuildRequires: python%{pyver}-devel
BuildRequires: python-setuptools
Requires: python%{pyver}
Requires: python-daemon
Requires: python%{pyver}-psutil

%description
A Red Hat Enterprise Linux-specific monitoring plugin for New Relic.

%prep
%setup -q -n %{name}-%{version}

%build
%{__python} setup.py build

%install
%{__rm} -rf %{buildroot}
%{__python} setup.py install -O1 --root=$RPM_BUILD_ROOT

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%config(noreplace) /etc/newrhelic.conf
/etc/init.d/newrhelic-plugin
%dir %{_docdir}/%{name}-%{version}
%{_docdir}/%{name}-%{version}/*
%{python_sitelib}/*egg-info
%{python_sitelib}/newrhelic*
%{_bindir}/newrhelic

%changelog
* Thu Jun 12 2014 Tommy McNeely <tommy@lark-it.com> 0.1-14
- attempts at making the same spec file work for EL5 and EL6

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
