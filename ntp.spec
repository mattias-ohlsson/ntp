%define	_bindir	%{_prefix}/sbin

Summary: Synchronizes system time using the Network Time Protocol (NTP).
Name: ntp
Version: 4.0.99k
Release: 15a
Copyright: distributable
Group: System Environment/Daemons
Source0: ftp://ftp.udel.edu/pub/ntp/ntp4/ntp-%{version}.tar.gz
Source1: ntp.conf
Source2: ntp.keys
Source3: ntpd.init
Patch0: ntp-4.0.99j-glibc22.patch
Patch1: ntp-4.0.99j-vsnprintf.patch
Patch2: ntp-4.0.99k-typos.patch
Patch3: ntp-4.0.99k-usegethost.patch
Patch4: ntp-4.0.99k-security.patch
URL: http://www.cis.udel.edu/~ntp
PreReq: /sbin/chkconfig
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
%patch2 -p1 -b .typos
%patch3 -p1 -b .usegethost
%patch4 -p1 -b .security

%build
# like libtoolize, but different
%ifarch s390 s390x
for file in config.sub config.guess ; do
  for place in `find . -type f -name $file` ; do
     cp -f /usr/share/libtool/$file $place
  done
done
%endif

# XXX work around for anal ntp configure
%define	_target_platform	%{nil}
CFLAGS="-g -DDEBUG" ./configure --prefix=/usr
%undefine	_target_platform

# XXX workaround glibc-2.1.90 lossage for now.
# XXX still broken with glibc-2.1.94-2 and glibc-2.1.95-1
patch config.h < %PATCH0

make

%install
rm -rf $RPM_BUILD_ROOT

%makeinstall

{ cd $RPM_BUILD_ROOT

  mkdir -p .%{_sysconfdir}/{ntp,rc.d/init.d}
  install -m644 $RPM_SOURCE_DIR/ntp.conf .%{_sysconfdir}/ntp.conf
  touch .%{_sysconfdir}/ntp/drift
  install -m600 $RPM_SOURCE_DIR/ntp.keys .%{_sysconfdir}/ntp/keys
  touch .%{_sysconfdir}/ntp/step-tickers
  install -m755 $RPM_SOURCE_DIR/ntpd.init .%{_sysconfdir}/rc.d/init.d/ntpd

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
%config				%{_sysconfdir}/rc.d/init.d/ntpd
%config(noreplace)		%{_sysconfdir}/ntp.conf
%dir				%{_sysconfdir}/ntp/
%ghost %config(missingok)	%{_sysconfdir}/ntp/drift
%config(noreplace)		%{_sysconfdir}/ntp/keys
%ghost %config(missingok)	%{_sysconfdir}/ntp/step-tickers

%changelog
* Fri May  4 2001 Oliver Paukstadt <oliver.paukstadt@millenux.com>
- ported to IBM zSeries (s390x, 64 bit)

* Thu Apr  5 2001 Preston Brown <pbrown@redhat.com>
- security patch for ntpd

* Mon Mar 26 2001 Preston Brown <pbrown@redhat.com>
- don't run configure macro twice (#32804)

* Mon Mar  5 2001 Preston Brown <pbrown@redhat.com>
- allow comments in /etc/ntp/step-tickers file (#28786).
- need patch0 (glibc patch) on ia64 too

* Tue Feb 13 2001 Florian La Roche <Florian.LaRoche@redhat.de>
- also set prog=ntpd in initscript

* Tue Feb 13 2001 Florian La Roche <Florian.LaRoche@redhat.de>
- use "$prog" instead of "$0" for the init script

* Thu Feb  8 2001 Preston Brown <pbrown@redhat.com>
- i18n-neutral .init script (#26525)

* Tue Feb  6 2001 Preston Brown <pbrown@redhat.com>
- use gethostbyname on addresses in /etc/ntp.conf for ntptime command (#26250)

* Mon Feb  5 2001 Preston Brown <pbrown@redhat.com>
- start earlier and stop later (#23530)

* Mon Feb  5 2001 Bernhard Rosenkraenzer <bero@redhat.com>
- i18nize init script (#26078)

* Sat Jan  6 2001 Jeff Johnson <jbj@redhat.com>
- typo in ntp.conf (#23173).

* Mon Dec 11 2000 Karsten Hopp <karsten@redhat.de>
- rebuilt to fix permissions of /usr/share/doc/ntp-xxx

* Thu Nov  2 2000 Jeff Johnson <jbj@redhat.com>
- correct mis-spellings in ntpq.htm (#20007).

* Thu Oct 19 2000 Jeff Johnson <jbj@redhat.com>
- add %ghost /etc/ntp/drift (#15222).

* Wed Oct 18 2000 Jeff Johnson <jbj@redhat.com>
- comment out default values for keys, warn about starting with -A (#19316).
- take out -A from ntpd startup as well.
- update to 4.0.99k.

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
