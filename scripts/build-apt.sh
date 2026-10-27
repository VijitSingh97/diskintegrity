#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
version=$(cat VERSION)
: "${APT_SIGNING_FINGERPRINT:=35C62BA9B0F75F049EC1C2472AB8B7C6F47CE1B7}"
mkdir -p public
cp "dist/diskintegrity_${version}_all.deb" public/
cd public
gpg --batch --list-secret-keys "$APT_SIGNING_FINGERPRINT" >/dev/null
gpg --batch --armor --export "$APT_SIGNING_FINGERPRINT" > diskintegrity.asc
apt-ftparchive packages . > Packages
gzip -n -k -f Packages
apt-ftparchive -o APT::FTPArchive::Release::Origin=diskintegrity \
    -o APT::FTPArchive::Release::Label=diskintegrity \
    -o 'APT::FTPArchive::Release::Architectures=amd64 arm64 armhf all' \
    release . > Release
gpg --batch --yes --armor --local-user "$APT_SIGNING_FINGERPRINT" \
    --detach-sign --output Release.gpg Release
gpg --batch --yes --armor --local-user "$APT_SIGNING_FINGERPRINT" \
    --clearsign --output InRelease Release
