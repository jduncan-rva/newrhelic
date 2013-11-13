%define name NewRHELic
%define version 0.1
%define unmangled_version 0.1
%define release 3 

Summary: RHEL/CentOS monitoring plugin for New Relic
Name: %{name}
Version: %{version}
Release: %{release}_CMS
Source0: %{name}-%{unmangled_version}.tar.gz
License: UNKNOWN
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
Vendor: Jamie Duncan <jduncan@redhat.com>
Url: https://github.com/jduncan-rva/newRHELic

%description
UNKNOWN

%pre
if [ -a /tmp/newrhelic.pid ]
then
/sbin/service newhrelic-plugin stop

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

%config /etc/newrhelic.conf
%config /etc/init.d/newrhelic-plugin
%docdir /usr/share/doc/NewRHELic-0.1

%changelog
* Wed Nov 13 2013 jduncan@redhat.com
- initial CMS-specific buildout
- added lockfile module
- altered default config file to disable NFS by default
