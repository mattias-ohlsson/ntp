%define glibc_version %(rpm -q glibc | cut -d . -f 1-2 )
%define glibc21 %([ "%glibc_version" = glibc-2.1 ] && echo 1 || echo 0)
%define glibc22 %([ "%glibc_version" = glibc-2.2 ] && echo 1 || echo 0)
%define	_bindir	%{_prefix}/sbin

Summary: Synchronizes system time using the Network Time Protocol (NTP).
Name: ntp
Version: 4.1.1a
Release: 9
License: distributable
Group: System Environment/Daemons
#Source0: ftp://ftp.udel.edu/pub/ntp/ntp4/ntp-%{version}.tar.gz
Source0: ftp://ftp.udel.edu/pub/ntp/ntp4/ntp-4.1.1a.tar.gz
Source1: ntp.conf
Source2: ntp.keys
Source3: ntpd.init
Source4: ntpd.sysconfig
Patch1: ntp-4.0.99j-vsnprintf.patch
Patch3: ntp-4.0.99m-usegethost.patch
#Patch4: ntp-4.0.99m-rc2-droproot.patch
Patch5: ntp-4.1.0-multi.patch
Patch6: ntp-4.1.0b-rc1-droproot.patch
Patch7: ntp-4.1.0b-rc1-genkey.patch
Patch8: ntp-4.1.1a-genkey2.patch

URL: http://www.cis.udel.edu/~ntp
PreReq: /sbin/chkconfig
Prereq: /usr/sbin/groupadd /usr/sbin/useradd
PreReq: sed
%{!?nocap:Requires: libcap}
%{!?nocap:BuildPreReq: libcap-devel}
Obsoletes: xntp3
BuildRoot: %{_tmppath}/%{name}-root

%description
The Network Time Protocol (NTP) is used to synchronize a computer's
time with another reference time source. The ntp package contains
utilities and daemons that will synchronize your computer's time to
Coordinated Universal Time (UTC) via the NTP protocol and NTP servers.
The ntp package includes ntpdate (a program for retrieving the date
and time from remote machines via a network) and ntpd (a daemon which
continuously adjusts system time).

Install the ntp package if you need tools for keeping your system's
time synchronized via the NTP protocol.

%prep 
%setup -q -n ntp-4.1.1a

%patch1 -p1 -b .vsnprintf
%patch3 -p1 -b .usegethost
%{!?nocap:%patch6 -p1 -b .droproot}
%patch5 -p1 -b .multi
%patch7 -p1 -b .genkey
%patch8 -p1 -b .genkey2
libtoolize --copy --force
%build


perl -pi -e 's|INSTALL_STRIP_PROGRAM="\\\$\{SHELL\} \\\$\(install_sh\) -c -s|INSTALL_STRIP_PROGRAM="\${SHELL} \$(install_sh) -c|g' configure
# XXX work around for anal ntp configure
%define	_target_platform	%{nil}
export CFLAGS="-g -DDEBUG" 
%configure --sysconfdir=/etc/ntp --enable-all-clocks --enable-parse-clocks
unset CFLAGS
%undefine	_target_platform

# XXX workaround glibc-2.1.90 lossage for now.
# XXX still broken with glibc-2.1.94-2 and glibc-2.1.95-1
%if ! %{glibc21} && ! %{glibc22}
( echo '#undef HAVE_CLOCK_SETTIME';
echo '#undef HAVE_TIMER_CREATE';
echo '#undef HAVE_TIMER_SETTIME';
)>>config.h
%endif

# Remove -lreadline and -lrt from ntpd/Makefile
# I don't see them used...
perl -pi -e "s|LIBS = -lrt -lreadline|LIBS = |" ntpd/Makefile 

perl -pi -e "s|-lelf||" */Makefile
perl -pi -e "s|-Wcast-qual||" */Makefile
perl -pi -e "s|-Wconversion||" */Makefile

make

%install
rm -rf $RPM_BUILD_ROOT

%makeinstall sysconfdir=/etc/ntp

{ cd $RPM_BUILD_ROOT

  mkdir -p .%{_sysconfdir}/{ntp,rc.d/init.d}
  install -m644 $RPM_SOURCE_DIR/ntp.conf .%{_sysconfdir}/ntp.conf
  echo '0.0' >.%{_sysconfdir}/ntp/drift
  install -m600 $RPM_SOURCE_DIR/ntp.keys .%{_sysconfdir}/ntp/keys
  touch .%{_sysconfdir}/ntp/step-tickers
  install -m755 $RPM_SOURCE_DIR/ntpd.init .%{_sysconfdir}/rc.d/init.d/ntpd

  %{!?nocap:mkdir -p .%{_sysconfdir}/sysconfig}
  %{!?nocap:install -m644 %{SOURCE4} .%{_sysconfdir}/sysconfig/ntpd}

  strip .%{_bindir}/* || :
}

%clean
rm -rf $RPM_BUILD_ROOT

%{!?nocap:%pre}
%{!?nocap:/usr/sbin/groupadd -g 38 ntp  2> /dev/null || :}
%{!?nocap:/usr/sbin/useradd -u 38 -g 38 -s /sbin/nologin -M -r -d /etc/ntp ntp 2>/dev/null || :}

%post
/sbin/chkconfig --add ntpd
%{!?nocap:if [ -f /etc/ntp/drift ]; then}
%{!?nocap:	chown ntp.ntp /etc/ntp/drift || :}
%{!?nocap:fi}

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
%{!?nocap:%config(noreplace)	%{_sysconfdir}/sysconfig/ntpd}
%config(noreplace)		%{_sysconfdir}/ntp.conf
%dir	%{!?nocap:%attr(-,ntp,ntp)}   %{_sysconfdir}/ntp
%config(noreplace) %{!?nocap:%attr(644,ntp,ntp)} %verify(not md5 size mtime) %{_sysconfdir}/ntp/drift
%config(noreplace) %{!?nocap:%attr(-,ntp,ntp)} %{_sysconfdir}/ntp/keys
%config(noreplace) %{!?nocap:%attr(-,ntp,ntp)} %verify(not md5 size mtime) %{_sysconfdir}/ntp/step-tickers

%changelog
* Sat Aug 31 2002 Florian La Roche <Florian.LaRoche@redhat.de>
- add option -n to initscript to avoid DNS lookups #72756

* Fri Aug 23 2002 Jeremy Katz <katzj@redhat.com>
- service should fail to start ntpd if running ntpdate fails

* Tue Aug 20 2002 Harald Hoyer <harald@redhat.de>
- added two more 'echo's in the initscript

* Thu Aug 15 2002 Harald Hoyer <harald@redhat.de>
- added firewall opener in initscript

* Tue Jul 23 2002 Harald Hoyer <harald@redhat.de>
- removed libelf dependency
- removed stripping

* Fri Jun 21 2002 Tim Powers <timp@redhat.com>
- automated rebuild

* Tue Jun 11 2002 Harald Hoyer <harald@redhat.de> 4.1.1a-3
- refixed #46464
- another genkeys/snprintf bugfix

* Wed May 22 2002 Harald Hoyer <harald@redhat.de> 4.1.1a-1
- update to version 4.1.1a

* Mon Apr 08 2002 Harald Hoyer <harald@redhat.de> 4.1.1-1
- update to 4.1.1 (changes are minimal)
- more examples in default configuration

* Tue Apr 02 2002 Harald Hoyer <harald@redhat.de> 4.1.0b-6
- more secure default configuration (#62238)

* Mon Jan 28 2002 Harald Hoyer <harald@redhat.de> 4.1.0b-5
- more regex magic for the grep (#57837)

* Mon Jan 28 2002 Harald Hoyer <harald@redhat.de> 4.1.0b-4
- created drift with dummy value #58294
- grep for timeservers in ntp.conf also for ntpdate #57837
- check return value of ntpdate #58836

* Wed Jan 09 2002 Tim Powers <timp@redhat.com> 4.1.0b-3
- automated rebuild

* Tue Jan 08 2002 Harald Hoyer <harald@redhat.de> 4.1.0b-2
- added --enable-all-clocks --enable-parse-clocks (#57761)

* Tue Dec 13 2001 Harald Hoyer <harald@redhat.de> 4.1.0b-1
- bumped version
- fixed #57391, #44580
- set startup position to 58 after named

* Wed Sep 05 2001 Harald Hoyer <harald@redhat.de> 4.1.0-4
- fixed #53184

* Tue Sep 04 2001 Harald Hoyer <harald@redhat.de> 4.1.0-3
- fixed #53089 /bin/nologin -> /sbin/nologin

* Fri Aug 31 2001 Harald Hoyer <harald@redhat.de> 4.1.0-2
- fixed #50247 thx to <enrico.scholz@informatik.tu-chemnitz.de>

* Thu Aug 30 2001 Harald Hoyer <harald@redhat.de> 4.1.0-1
- wow, how stupid can a man be ;).. fixed #50698 
- updated to 4.1.0 (changes are small and in non-critical regions)

* Wed Aug 29 2001 Harald Hoyer <harald@redhat.de> 4.0.99mrc2-5
- really, really :) fixed #52763, #50698 and #50526

* Mon Aug 27 2001 Tim Powers <timp@redhat.com> 4.0.99mrc2-4
- rebuilt against newer libcap
- Copyright -> license

* Wed Jul 25 2001 Harald Hoyer <harald@redhat.com> 4.0.99mrc2-3
- integrated droproot patch (#35653)
- removed librt and libreadline dependency 

* Sat Jul  7 2001 Tim Powers <timp@redhat.com>
- don't build build sgid root dirs

* Mon Jun 18 2001 Harald Hoyer <harald@redhat.de>
- new snapshot
- removed typos and security patch (already there)
- commented multicastclient in config file

* Thu Jun 07 2001 Florian La Roche <Florian.LaRoche@redhat.de>
- call libtoolize to compile on newer archs

* Mon Apr  9 2001 Preston Brown <pbrown@redhat.com>
- remove ghost files make RHN happy
- modify initscript to match accordingly

* Fri Apr  6 2001 Pekka Savola <pekkas@netcore.fi>
- Add the remote root exploit patch (based on ntp-hackers).
- Enhance droproot patch (more documentation, etc.) <Jarno.Huuskonen@uku.fi>
- Tweak the droproot patch to include sys/prctl.h, not linux/prctl.h
(implicit declarations)
- Remote groupdel commands, shouldn't be needed.
- Removed -Wcast-qual and -Wconversion due to excessive warnings (hackish).
- Make ntp compilable with both glibc 2.1 and 2.2.x (very dirty hack)
- Add /etc/sysconfig/ntpd which drops root privs by default

* Thu Apr  5 2001 Preston Brown <pbrown@redhat.com>
- security patch for ntpd

* Mon Mar 26 2001 Preston Brown <pbrown@redhat.com>
- don't run configure macro twice (#32804)

* Sun Mar 25 2001 Pekka Savola <pekkas@netcore.fi>
- require/buildprereq libcap/libcap-devel
- use 'ntp' user, tune the pre/post scripts, %%files
- add $OPTIONS to the init script

* Tue Mar 20 2001 Jarno Huuskonen <Jarno.Huuskonen@uku.fi>
- droproot/caps patch
- add ntpd user in pre
- make /etc/ntp ntpd writable

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
