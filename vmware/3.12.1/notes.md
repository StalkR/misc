vmhgfs from VMware Tools 9.6.0 build-1294478 fails to compile on 3.12.1:

    # vmware-config-tools.pl
    [...]
    Using 2.6.x kernel build system.
    make: Entering directory `/tmp/modconfig-qmJ93V/vmhgfs-only'
    /usr/bin/make -C /lib/modules/3.12-1-amd64/build/include/.. SUBDIRS=$PWD SRCROOT=$PWD/. \
              MODULEBUILDDIR= modules
    make[1]: Entering directory `/usr/src/linux-headers-3.12-1-amd64'
      CC [M]  /tmp/modconfig-qmJ93V/vmhgfs-only/backdoor.o
      CC [M]  /tmp/modconfig-qmJ93V/vmhgfs-only/backdoorGcc64.o
      CC [M]  /tmp/modconfig-qmJ93V/vmhgfs-only/bdhandler.o
      CC [M]  /tmp/modconfig-qmJ93V/vmhgfs-only/cpName.o
      CC [M]  /tmp/modconfig-qmJ93V/vmhgfs-only/cpNameLinux.o
      CC [M]  /tmp/modconfig-qmJ93V/vmhgfs-only/cpNameLite.o
      CC [M]  /tmp/modconfig-qmJ93V/vmhgfs-only/dentry.o
      CC [M]  /tmp/modconfig-qmJ93V/vmhgfs-only/dir.o
      CC [M]  /tmp/modconfig-qmJ93V/vmhgfs-only/file.o
    /tmp/modconfig-qmJ93V/vmhgfs-only/file.c: In function ‘HgfsOpen’:
    /tmp/modconfig-qmJ93V/vmhgfs-only/file.c:659:27: error: incompatible type for argument 3 of ‘HgfsSetUidGid’
                               current_fsuid(), current_fsgid());
                               ^
    In file included from /tmp/modconfig-qmJ93V/vmhgfs-only/file.c:46:0:
    /tmp/modconfig-qmJ93V/vmhgfs-only/fsutil.h:92:6: note: expected ‘uid_t’ but argument is of type ‘kuid_t’
     void HgfsSetUidGid(struct inode *parent,
          ^
    /tmp/modconfig-qmJ93V/vmhgfs-only/file.c:659:27: error: incompatible type for argument 4 of ‘HgfsSetUidGid’
                               current_fsuid(), current_fsgid());
                               ^
    In file included from /tmp/modconfig-qmJ93V/vmhgfs-only/file.c:46:0:
    /tmp/modconfig-qmJ93V/vmhgfs-only/fsutil.h:92:6: note: expected ‘gid_t’ but argument is of type ‘kgid_t’
     void HgfsSetUidGid(struct inode *parent,
          ^
    make[4]: *** [/tmp/modconfig-qmJ93V/vmhgfs-only/file.o] Error 1
    make[3]: *** [_module_/tmp/modconfig-qmJ93V/vmhgfs-only] Error 2
    make[2]: *** [sub-make] Error 2
    make[1]: *** [all] Error 2
    make[1]: Leaving directory `/usr/src/linux-headers-3.12-1-amd64'
    make: *** [vmhgfs.ko] Error 2
    make: Leaving directory `/tmp/modconfig-qmJ93V/vmhgfs-only'
    [...]


Make sure you have kernel headers:

    # dpkg -l | egrep 'linux-(image|headers)'
    ii  linux-headers-3.12-1-amd64   3.12.6-1  amd64  Header files for Linux 3.12-1-amd64
    ii  linux-headers-3.12-1-common  3.12.6-1  amd64  Common header files for Linux 3.12-1
    ii  linux-image-3.12-1-amd64     3.12.6-1  amd64  Linux 3.12 for 64-bit PCs

Patch to use new dentry count and kuid_t/kgid_t:

    tar xf /usr/lib/vmware-tools/modules/source/vmhgfs.tar -C /tmp
    pushd /tmp/vmhgfs-only
    curl https://raw.github.com/StalkR/misc/master/vmware/3.12.1/vmhgfs.patch | patch
    popd
    tar cf /usr/lib/vmware-tools/modules/source/vmhgfs.tar -C /tmp vmhgfs-only
    rm -rf /tmp/vmhgfs-only

Manual make for testing:

    tar xf /usr/lib/vmware-tools/modules/source/vmhgfs.tar -C /tmp
    make -j1 -C /tmp/vmhgfs-only auto-build HEADER_DIR=/lib/modules/$(uname -r)/build/include CC=/usr/bin/gcc IS_GCC_3=no
