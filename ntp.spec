%define _use_internal_dependency_generator 0
%define glibc_version %(rpm -q glibc | cut -d . -f 1-2 )
%define glibc21 %([ "%glibc_version" = glibc-2.1 ] && echo 1 || echo 0)
%define glibc22 %([ "%glibc_version" = glibc-2.2 ] && echo 1 || echo 0)

%define tarversion stable-4.2.0a-20050816

Summary: Synchronizes system time using the Network Time Protocol (NTP).
Name: ntp
Version: 4.2.0.a.20050816
Release: 1
License: distributable
Group: System Environment/Daemons
Source0: http://www.eecis.udel.edu/~ntp/ntp_spool/ntp4/ntp-%{tarversion}.tar.gz
Source1: ntp.conf
Source2: ntp.keys
Source3: ntpd.init
Source4: ntpd.sysconfig
Source5: ntpstat-0.2.tgz
Source6: ntp-4.2.0-rh-manpages.tar.gz

# new find-requires
Source7: filter-requires-ntp.sh
%define __find_requires %{SOURCE7}

Patch1: ntp-4.0.99m-usegethost.patch
Patch2: ntp-4.2.0-droproot.patch
Patch3: ntp-stable-4.2.0a-20040616-groups.patch
Patch4: ntp-4.1.1c-rc3-authkey.patch
Patch5: ntp-4.2.0-md5.patch
Patch6: ntp-4.2.0-genkey3.patch
Patch7: ntp-4.2.0-sbinpath.patch
Patch8: ntp-stable-4.2.0a-20040617-Wall.patch
Patch9: ntp-stable-4.2.0a-20040617-ntpd_guid.patch

URL: http://www.ntp.org
PreReq: /sbin/chkconfig
Prereq: /usr/sbin/groupadd /usr/sbin/useradd
PreReq: /bin/awk sed grep
Requires: libcap
BuildRequires: libcap-devel autoconf automake openssl-devel
BuildRequires: readline-devel
Obsoletes: xntp3 ntpstat
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
%setup -q -n ntp-%{tarversion} -a 5 -a 6

%patch1 -p1 -b .usegethost
%patch2 -p1
%patch3 -p1 -b .groups
%patch4 -p1 -b .authkey
%patch5 -p1 -b .nomd5lib
%patch6 -p1 -b .genkey3
%patch7 -p1 -b .sbinpath
%patch8 -p1 -b .wall
%patch9 -p1 -b .noguid
%build


perl -pi -e 's|INSTALL_STRIP_PROGRAM="\\\$\{SHELL\} \\\$\(install_sh\) -c -s|INSTALL_STRIP_PROGRAM="\${SHELL} \$(install_sh) -c|g' configure
# XXX work around for anal ntp configure
%define	_target_platform	%{nil}
export CFLAGS="$RPM_OPT_FLAGS -g -DDEBUG -D_FORTIFYSOURCE=2 -Wall" 
if echo 'int main () { return 0; }' | gcc -pie -fPIE -O2 -xc - -o pietest 2>/dev/null; then
	./pietest && export CFLAGS="$CFLAGS -pie -fPIE"
	rm -f pietest
fi
%configure --sysconfdir=%{_sysconfdir}/ntp --bindir=%{_sbindir} --enable-all-clocks --enable-parse-clocks --with-openssl-libdir=%{_libdir} --enable-linuxcaps
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

make Makefile
for dir in *; do 
	[ -d $dir ] && make -C $dir Makefile || :
done

# Remove -lreadline and -lrt from ntpd/Makefile
# I don't see them used...
perl -pi -e "s|LIBS = -lrt -lreadline|LIBS = |" ntpd/Makefile 

perl -pi -e "s|-lelf||" */Makefile
perl -pi -e "s|-Wcast-qual||" */Makefile
perl -pi -e "s|-Wconversion||" */Makefile
find . -name Makefile -print0 | xargs -0 perl -pi -e "s|-Wall|-Wall -Wextra -Wno-unused|g"

make
pushd ntpstat-0.2
make
popd


%install
rm -rf $RPM_BUILD_ROOT

%makeinstall sysconfdir=%{_sysconfdir}/ntp bindir=${RPM_BUILD_ROOT}%{_sbindir}

pushd ntpstat-0.2
mkdir -p ${RPM_BUILD_ROOT}/%{_mandir}/man1
mkdir -p ${RPM_BUILD_ROOT}/%{_bindir}

install -m 755 ntpstat ${RPM_BUILD_ROOT}/%{_bindir}/
install -m 644 ntpstat.1 ${RPM_BUILD_ROOT}/%{_mandir}/man1/
popd
pushd man
for i in *.1; do 
	install -m 644 $i ${RPM_BUILD_ROOT}/%{_mandir}/man1/
done

{ cd $RPM_BUILD_ROOT

  mkdir -p .%{_sysconfdir}/ntp
  mkdir -p .%{_initrddir}
  install -m644 $RPM_SOURCE_DIR/ntp.conf .%{_sysconfdir}/ntp.conf
  mkdir -p .%{_var}/lib/ntp
  echo '0.0' >.%{_var}/lib/ntp/drift
  install -m600 $RPM_SOURCE_DIR/ntp.keys .%{_sysconfdir}/ntp/keys
  touch .%{_sysconfdir}/ntp/step-tickers
  install -m755 $RPM_SOURCE_DIR/ntpd.init .%{_initrddir}/ntpd

  mkdir -p .%{_sysconfdir}/sysconfig
  install -m644 %{SOURCE4} .%{_sysconfdir}/sysconfig/ntpd
}


%clean
rm -rf $RPM_BUILD_ROOT

%pre
/usr/sbin/groupadd -g 38 ntp  2> /dev/null || :
/usr/sbin/useradd -u 38 -g 38 -s /sbin/nologin -M -r -d %{_sysconfdir}/ntp ntp 2>/dev/null || :

%post
/sbin/chkconfig --add ntpd

if [ "$1" -ge "1" ]; then
  grep %{_sysconfdir}/ntp/drift %{_sysconfdir}/ntp.conf > /dev/null 2>&1
  olddrift=$?
  if [ $olddrift -eq 0 ]; then
    service ntpd status > /dev/null 2>&1
    wasrunning=$?
    # let ntp save the actual drift
    [ $wasrunning -eq 0 ] && service ntpd stop > /dev/null 2>&1
    # copy the driftfile to the new location
    [ -f %{_sysconfdir}/ntp/drift ] \
      && cp %{_sysconfdir}/ntp/drift %{_var}/lib/ntp/drift
    # change the path in the config file
    sed -e 's#%{_sysconfdir}/ntp/drift#%{_var}/lib/ntp/drift#g' \
      %{_sysconfdir}/ntp.conf > %{_sysconfdir}/ntp.conf.rpmupdate \
      && mv %{_sysconfdir}/ntp.conf.rpmupdate %{_sysconfdir}/ntp.conf 
    # remove the temp file
    rm -f %{_sysconfdir}/ntp.conf.rpmupdate
    # start ntp if it was running previously
    [ $wasrunning -eq 0 ] && service ntpd start > /dev/null 2>&1
  fi
fi


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
%{_sbindir}/ntp-wait
%{_sbindir}/ntptrace
%{_sbindir}/ntp-keygen
%{_sbindir}/ntpd
%{_sbindir}/ntpdate
%{_sbindir}/ntpdc
%{_sbindir}/ntpq
%{_sbindir}/ntptime
%{_sbindir}/tickadj
%config			%{_initrddir}/ntpd
%config(noreplace)	%{_sysconfdir}/sysconfig/ntpd
%config(noreplace)	%{_sysconfdir}/ntp.conf
%dir 	%{_sysconfdir}/ntp
%config(noreplace) %verify(not md5 size mtime) %{_sysconfdir}/ntp/step-tickers
%config(noreplace) %{_sysconfdir}/ntp/keys
%dir	%attr(-,ntp,ntp)   %{_var}/lib/ntp
%config(noreplace) %attr(644,ntp,ntp) %verify(not md5 size mtime) %{_var}/lib/ntp/drift
%{_mandir}/man1/*
%{_bindir}/ntpstat


%changelog
* Thu Aug 25 2005 Jindrich Novy <jnovy@redhat.com> 4.2.0.a.20050816-1
- update to the latest stable 4.2.0.a.20050816
- drop upstreamed .gcc4, .vsnprintf patches
- remove obsolete .autofoo patch
- make patch numbering less chaotic
- don't package backup for .droproot patch

* Thu Apr 14 2005 Jiri Ryska <jryska@redhat.com> 4.2.0.a.20040617-8
- fixed gid setting when ntpd started with -u flag

* Tue Mar 08 2005 Jiri Ryska <jryska@redhat.com> 4.2.0.a.20040617-7
- removed -Werror
- patched for gcc4 and rebuilt

* Wed Jan 12 2005 Tim Waugh <twaugh@redhat.com> - 4.2.0.a.20040617-6
- Rebuilt for new readline.

* Mon Dec 13 2004 Harald Hoyer <harald@redhat.com> - 4.2.0.a.20040617-5
- patched ntp to build with -D_FORTIFYSOURCE=2 -Wall -Wextra -Werror

* Mon Oct 11 2004 Harald Hoyer <harald@redhat.com> - 4.2.0.a.20040617-4
- removed firewall hole punching from the initscript; rely on iptables
  ESTABLISHED,RELATED or manual firewall configuration

* Fri Oct  8 2004 Harald Hoyer <harald@redhat.com> - 4.2.0.a.20040617-3
- improved postsection
- BuildRequires readline-devel
- PreReq grep

* Thu Sep 30 2004 Harald Hoyer <harald@redhat.com> - 4.2.0.a.20040617-2
- set pool.ntp.org as the default timeserver pool

* Mon Sep 13 2004 Harald Hoyer <harald@redhat.com> - 4.2.0.a.20040617-1
- version ntp-stable-4.2.0a-20040617

* Tue Aug 17 2004 Harald Hoyer <harald@redhat.com> - 4.2.0.a.20040616-4
- added ntp-4.2.0-sbinpath.patch (bug 130536)

* Tue Aug 17 2004 Harald Hoyer <harald@redhat.com> - 4.2.0.a.20040616-3
- added ntp-stable-4.2.0a-20040616-groups.patch (bug 130112)

* Thu Jul 29 2004 Harald Hoyer <harald@redhat.com> - 4.2.0.a.20040616-2
- take chroot in account (bug 127252)

* Fri Jul 23 2004 Harald Hoyer <harald@redhat.com> - 4.2.0.a.20040616-1
- new version ntp-stable-4.2.0a-20040616
- removed most patches

* Tue Jun 15 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Thu Mar 11 2004 Harald Hoyer <harald@redhat.com> - 4.2.0-7
- ntpgenkey fixed (117378)
- fixed initscript to call ntpdate with -U (117894)

* Fri Feb 13 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Wed Jan 28 2004 Harald Hoyer <harald@faro.stuttgart.redhat.com> - 4.2.0-5
- readded ntp-wait and ntptrace
- new filter-requires to prevent perl dependency

* Mon Jan 26 2004 Harald Hoyer <harald@redhat.de> 4.2.0-4
- added autofoo patch

* Tue Oct 28 2003 Harald Hoyer <harald@redhat.de> 4.2.0-3
- removed libmd5 dependency
- removed perl dependency

* Tue Oct 28 2003 Harald Hoyer <harald@redhat.de> 4.2.0-2
- fixed initscript to use new FW chain name

* Mon Oct 27 2003 Harald Hoyer <harald@redhat.de> 4.2.0-1
- 4.2.0
- added PIE

* Thu Sep 11 2003 Harald Hoyer <harald@redhat.de> 4.1.2-4
- changed ntp.conf driftfile path #104207

* Fri Aug 29 2003 Florian La Roche <Florian.LaRoche@redhat.de>
- also build as non-root

* Thu Aug 28 2003 Harald Hoyer <harald@redhat.de> 0:4.1.2-2
- added ntpstat
- added manpages

* Wed Jul 01 2003 Harald Hoyer <harald@redhat.de> 0:4.1.2-1.rc3.5
- move driftfile to /var

* Wed Jul 01 2003 Harald Hoyer <harald@redhat.de> 0:4.1.2-1.rc3.4
- make a seperate directory for drift
- security fix, patch ntp-4.1.1c-rc3-authkey.patch #96927
 
* Wed Jun 18 2003 Harald Hoyer <harald@redhat.de> 0:4.1.2-1.rc3.3
- %%{_sysconfdir}/ntp/drift.TEMP needs to be writable by ntp #97754
- no duplicate fw entries #97624

* Wed Jun 18 2003 Harald Hoyer <harald@redhat.de> 0:4.1.2-1.rc3.2
- changed permissions of config files  

* Tue Jun 17 2003 Harald Hoyer <harald@redhat.de> 0:4.1.2-1.rc3.1
- updated to rc3 

* Wed Jun 04 2003 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Thu May 22 2003 Harald Hoyer <harald@redhat.de> 0:4.1.2-0.rc2.2
- corrected pid file name in %%{_sysconfdir}/sysconfig/ntpd

* Tue Apr 28 2003 Harald Hoyer <harald@redhat.de> 0:4.1.2-0.rc2.1
- update to 4.1.1rc2

* Tue Feb 25 2003 Harald Hoyer <harald@redhat.de> 0:4.1.2-0.rc1.3
- better awk for timeservers #85090, #82713, #82714

* Thu Feb 13 2003 Harald Hoyer <harald@redhat.de> 0:4.1.2-0.rc1.2
- added loopfilter patch, -x should work now!
- removed slew warning

* Mon Feb 10 2003 Harald Hoyer <harald@redhat.de> 1:4.1.1-2
- ok, messed up with the versions... added epoch :(

* Fri Feb 07 2003 Harald Hoyer <harald@redhat.de> 4.1.1-1
- going back to stable 4.1.1 with the limit patch
- added limit patch
- added slew warning

* Thu Jan 30 2003 Harald Hoyer <harald@redhat.de> 4.1.73-2
- removed exit on ntpdate fail, better add '-g' option

* Wed Jan 29 2003 Harald Hoyer <harald@redhat.de> 4.1.73-1
- update to version 4.1.73
- removed most of the patches
- limit ntp_adjtime parameters

* Wed Jan 22 2003 Tim Powers <timp@redhat.com>
- rebuilt

* Wed Nov 20 2002 Harald Hoyer <harald@redhat.de> 4.1.1b-1
- updated to version 4.1.1b
- improved initscript - use ntpdate on -x
- improved initscript - open firewall only for timeservers
- ntp-4.1.1a-adjtime.patch removed (already in source)
- ntp-4.1.1a-mfp.patch removed (already in source)
- ntp-4.0.99j-vsnprintf.patch removed (already in source)

* Tue Nov 19 2002 Harald Hoyer <harald@redhat.de> 4.1.1a-12
- added adjtime patch #75558

* Wed Nov 13 2002 Harald Hoyer <harald@redhat.de>
- more ntpd.init service description #77715

* Mon Nov 11 2002 Harald Hoyer <harald@redhat.de>
- ntp-4.1.1a-mfp.patch fixes #77086

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
- Add %%{_sysconfdir}/sysconfig/ntpd which drops root privs by default

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
- make %%{_sysconfdir}/ntp ntpd writable

* Mon Mar  5 2001 Preston Brown <pbrown@redhat.com>
- allow comments in %%{_sysconfdir}/ntp/step-tickers file (#28786).
- need patch0 (glibc patch) on ia64 too

* Tue Feb 13 2001 Florian La Roche <Florian.LaRoche@redhat.de>
- also set prog=ntpd in initscript

* Tue Feb 13 2001 Florian La Roche <Florian.LaRoche@redhat.de>
- use "$prog" instead of "$0" for the init script

* Thu Feb  8 2001 Preston Brown <pbrown@redhat.com>
- i18n-neutral .init script (#26525)

* Tue Feb  6 2001 Preston Brown <pbrown@redhat.com>
- use gethostbyname on addresses in %%{_sysconfdir}/ntp.conf for ntptime command (#26250)

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
- add %ghost %%{_sysconfdir}/ntp/drift (#15222).

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
