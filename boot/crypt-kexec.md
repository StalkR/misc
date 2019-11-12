# Full disk encryption with kexec

In this setup the entire disk is encrypted, there is not even a /boot.
It works by booting the machine in rescue mode or on a live cd/usb, unlocking
the encrypted device and kexec the kernel and its initramfs.

## Creating the encrypted device

If you already have an existing system, adjust steps as necessary.

Boot in rescue or on a live cd/usb then partition the disk:

```
cfdisk /dev/sda
```

We will assume a single partition `/dev/sda1` is created.

Create the encrypted LUKS partition, choose a passphrase:

```
cryptsetup luksFormat /dev/sda1
```

Unlock it:

```
cryptsetup luksOpen /dev/sda1 crypt
```

Create a filesystem:

```
mkfs.ext4 /dev/mapper/crypt
```

Mount it:

```
mount /dev/mapper/crypt /mnt
```

## Installing a system

From now on, install as you normally would.
As an example, let's install Debian 10 (buster).

Set a hostname on the temporary host so the new system inherits it later:
```
echo 'example.net' > /etc/hostname
hostname -F /etc/hostname
```

Use debootstrap to install Debian:

```
debootstrap buster /mnt
```

Enter the chroot to continue installing:

```
mount -o bind /dev /mnt/dev
chroot /mnt /bin/bash
mount -t proc proc /proc
mount -t sysfs sys /sys
mount -t devpts devpts /dev/pts
```

Configure a root password:

```
passwd
```

Set up fstab:

```
cat << EOF > /etc/fstab
/dev/mapper/crypt / ext4 errors=remount-ro 0 1
EOF
```

And many other things like networking, etc.

## Installing tools

Install a kernel, cryptsetup and kexec-tools:

```
apt install -y linux-image-amd64 cryptsetup kexec-tools
```

You can configure `kexec-tools` package like this:

```
dpkg-reconfigure kexec-tools
# Should kexec-tools handle reboots (sysvinit only)? yes
# Read GRUB configuration file to load the kernel? no (edit /etc/default/kexec directly)
```

## Preparing the initramfs

Now we get to the interesting part: preparing the initramfs so that it
automatically unlocks the encrypted device.

Create a directory to hold key files, generate a random key file and add it to
the LUKS device:

```
mkdir -p /etc/keys
chmod 700 /etc/keys
head -c 32 /dev/urandom | sha256sum | cut -d' ' -f1 > /etc/keys/cryptroot
chmod 600 /etc/keys/cryptroot
cryptsetup luksAddKey /dev/sda1 /etc/keys/cryptroot
```

Configure crypttab:

```
cat << EOF > /etc/crypttab
# <target name> <source device>         <key file>          <options>
crypt           /dev/sda1               /etc/keys/cryptroot luks
EOF
```

Note: instead of `/dev/sda1` you can use UUID=X as identified by `blkid`, it is
more robust when device order changes.

Configure initramfs to use cryptsetup, find the key files and restrict the
resulting file in `/boot` to root not to leak them:

```
sed -i 's,^#CRYPTSETUP=,CRYPTSETUP=y,' /etc/cryptsetup-initramfs/conf-hook
sed -i 's,^#KEYFILE_PATTERN=,KEYFILE_PATTERN=/etc/keys/*,' /etc/cryptsetup-initramfs/conf-hook
echo 'UMASK=0077' > /etc/initramfs-tools/conf.d/umask.conf
```

Update initramfs with our modifications:

```
update-initramfs -tuck $(dpkg -l | awk '$2~"^linux-image-[0-9]+"{print substr($2,13)}')
```

## Rebooting with kexec

Use [kexec(8)](kexec) to load a new kernel and initramfs then execute it:

[kexec]: https://linux.die.net/man/8/kexec

```
kexec -l /boot/vmlinuz-4.19.0-6-amd64 --initrd=/boot/initrd.img-4.19.0-6-amd64 --append=''
kexec -e
```

You can use `--append=''` to set kernel command-line parameters, for example:

```
--append='root=/dev/mapper/crypt console=tty0 debug ro acpi=off'
```

Alternatively, use `--reuse-cmdline` to reuse the current kernel command-line,
which makes sense if you are already on the final system but less from the
rescue or live cd/usb system.

If kexec works, it should boot the new kernel.
It doesn't work on some hardware or virtual machines, I don't know why.

If the initramfs works, it should unlock the encrypted device and boot with
this filesystem.

## Debugging

Boot the rescue or live cd/usb with kernel command-line `debug` option, so
you see better what happens at `kexec`.

Use option `-d` for debugging of kexec: `kexec -d -e`.

## Other documentation

- <https://wiki.archlinux.org/index.php/kexec>
