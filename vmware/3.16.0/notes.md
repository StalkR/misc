vmhgfs from VMware Tools 9.6.0 build-1294478 fails to compile on 3.16.0-4:

    # vmware-config-tools.pl
    [...] errors


Make sure you have kernel headers:

    # dpkg -l | egrep 'linux-(image|headers)'

Patch:

    tar xf /usr/lib/vmware-tools/modules/source/vmhgfs.tar -C /tmp
    pushd /tmp/vmhgfs-only
    curl https://raw.githubusercontent.com/StalkR/misc/master/vmware/3.16.0/vmhgfs.patch | patch -p1
    popd
    tar cf /usr/lib/vmware-tools/modules/source/vmhgfs.tar -C /tmp vmhgfs-only
    rm -rf /tmp/vmhgfs-only

Manual make for testing:

    tar xf /usr/lib/vmware-tools/modules/source/vmhgfs.tar -C /tmp
    make -j1 -C /tmp/vmhgfs-only auto-build HEADER_DIR=/lib/modules/$(uname -r)/build/include CC=/usr/bin/gcc IS_GCC_3=no
