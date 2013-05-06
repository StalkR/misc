#!/bin/bash
# Get linux to recognize go script and "go run" it using binfmt.

apt-get install binfmt-support

cat > /usr/local/bin/gorun << EOF
#!/bin/sh
/usr/bin/go run "\$@"
EOF

chmod 755 /usr/local/bin/gorun

update-binfmts --install go /usr/local/bin/gorun --extension go
