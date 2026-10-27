#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
version=$(cat VERSION)
SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH:-$(git log -1 --format=%ct)}
export SOURCE_DATE_EPOCH
package=$(mktemp -d)
trap 'rm -rf "$package"' EXIT
make install DESTDIR="$package" PREFIX=/usr ZSH_COMPLETION_DIR=/usr/share/zsh/vendor-completions
install -d "$package/DEBIAN" "$package/usr/share/doc/diskintegrity"
install -m 644 LICENSE "$package/usr/share/doc/diskintegrity/copyright"
cat > "$package/DEBIAN/control" <<CONTROL
Package: diskintegrity
Version: $version
Section: utils
Priority: optional
Architecture: all
Maintainer: Vijit Singh <VijitSingh97@users.noreply.github.com>
Depends: python3 (>= 3.10), smartmontools, sudo, util-linux
Homepage: https://github.com/VijitSingh97/diskintegrity
Description: Check disk health with surface scans, SMART data, and a PASS/FAIL report
 Checks physical disks with read-only scans or an explicit destructive write test.
 Includes Zsh completion.
CONTROL
mkdir -p dist
dpkg-deb --root-owner-group --build "$package" "dist/diskintegrity_${version}_all.deb"
