%define	_bindir	%{_prefix}/sbin

Summary: Synchronizes system time using the Network Time Protocol (NTP).
Name: ntp
Version: 4.0.99j
Release: 7
Copyright: distributable
Group: System Environment/Daemons
Source0: ftp://ftp.udel.edu/pub/ntp/ntp4/ntp-%{version}.tar.gz
Source1: ntp.conf
Source2: ntp.keys
Source3: ntpd.rc
Patch0: ntp-4.0.99j-glibc22.patch
Patch1: ntp-4.0.99j-vsnprintf.patch
URL: http://www.cis.udel.edu/~ntp
Prereq: /sbin/chkconfig /etc/init.d
#Conflicts: xntp3
Obsoletes: xntp3
BuildRoot: %{_tmppath}/%{name}-root

%description
The Network Time Protocol (NTP) is used to synchronize a computer's
time with another reference time source.  The ntp package contains
utilities and daemons which will synchronize your computer's time to
Coordinated Universal Time (UTC) via the NTP protocol and NTP servers.
The ntp package includes ntpdate (a program for retrieving the date
and time from remote machines via a network) and ntpd (a daemon which
continuously adjusts system time).

Install the ntp package if you need tools for keeping your system's
time synchronized via the NTP protocol.

%prep 
%setup -q 

%patch1 -p1 -b .vsnprintf

%build

# XXX work around for anal ntp configure
%define	_target_platform	%{nil}
%configure
%undefine	_target_platform

# XXX workaround glibc-2.1.90 lossage for now.
%ifnarch ia64
patch config.h < %PATCH0
%endif

make

%install
rm -rf $RPM_BUILD_ROOT

%makeinstall

{ cd $RPM_BUILD_ROOT

  mkdir -p .%{_sysconfdir}/{ntp,rc.d/init.d}
  install -m644 $RPM_SOURCE_DIR/ntp.conf .%{_sysconfdir}/ntp.conf
  install -m600 $RPM_SOURCE_DIR/ntp.keys .%{_sysconfdir}/ntp/keys
  touch .%{_sysconfdir}/ntp/step-tickers
  install -m755 $RPM_SOURCE_DIR/ntpd.rc .%{_sysconfdir}/rc.d/init.d/ntpd

  strip .%{_bindir}/* || :
}

%clean
rm -rf $RPM_BUILD_ROOT

%post
/sbin/chkconfig --add ntpd

%preun
if [ $1 = 0 ]; then
    service ntpd stop > /dev/null 2>&1
    /sbin/chkconfig --del ntpd
fi

%postun
if [ "$1" -ge "1" ]; then
  service ntpd condrestart > /dev/null 2>&1
fi

%files
%defattr(-,root,root)
%doc html/* NEWS TODO 
%{_bindir}/*
%config		%{_sysconfdir}/rc.d/init.d/ntpd
%config(noreplace)		%{_sysconfdir}/ntp.conf
%config(noreplace)		%{_sysconfdir}/ntp/keys
%ghost %config(missingok) %{_sysconfdir}/ntp/step-tickers

%changelog
* Wed Aug 23 2000 Jeff Johnson <jbj@redhat.com>
- use vsnprintf rather than vsprintf (#16676).

* Mon Aug 14 2000 Jeff Johnson <jbj@redhat.com>
- remove Conflicts: so that the installer is happy.

* Tue Jul 25 2000 Jeff Johnson <jbj@redhat.com>
- workaround glibc-2.1.90 lossage for now.

* Thu Jul 20 2000 Bill Nottingham <notting@redhat.com>
- move initscript back

* Wed Jul 12 2000 Prospector <bugzilla@redhat.com>
- automatic rebuild

* Mon Jun 26 2000 Preston Brown <pbrown@redhat.com>
- move and update init script, update post/preun/postun scripts

* Wed Jun 21 2000 Preston Brown <pbrown@redhat.com>
- noreplace ntp.conf,keys files

* Mon Jun 12 2000 Jeff Johnson <jbj@redhat.com>
- Create 4.0.99j package.
- FHS packaging.
