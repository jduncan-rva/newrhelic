%define name NewRHELic
%define version 0.1
%define unmangled_version 0.1
%define release 11

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
A RHEL 6/CentOS 6-specific monitoring plugin for New Relic (http://www.newrelic.com)

%prep
%setup -n %{name}-%{unmangled_version}

%build
env CFLAGS="$RPM_OPT_FLAGS" python setup.py build

%install
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
%config(noreplace) /etc/newrhelic.conf

%postun

%changelog
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
