%define name NewRHELic
%define version 0.1
%define unmangled_version 0.1
%define release 13

Summary: RHEL/CentOS monitoring plugin for New Relic
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
License: GPLv2
Group: Monitoring
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
Vendor: Jamie Duncan <jduncan@redhat.com>
Packager: Jamie Duncan <jduncan@redhat.com>
Url: https://github.com/jduncan-rva/newRHELic

%description
A Red Hat Enterprise Linux-specific monitoring plugin for New Relic (http://www.newrelic.com). A Red Hat Community supported project. Details at http://newrelic.com/plugins/jamie-duncan/154. Currently working for RHEL 6 only.

%pre
if [ -a '/tmp/newrhelic.pid' ]
then
/sbin/service newrhelic-plugin stop
fi

%prep
%setup -n %{name}-%{unmangled_version}

%build
env CFLAGS="$RPM_OPT_FLAGS" python setup.py build

%install
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%post
/sbin/chkconfig newrhelic-plugin on
/sbin/service newrhelic-plugin start

%files -f INSTALLED_FILES
%defattr(-,root,root)
%config(noreplace) /etc/newrhelic.conf

%postun

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
