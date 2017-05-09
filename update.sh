#!/bin/bash


STATE=stable
MAJORVER=8

# Latest MOSEK distro version
MOSEKVER=$(curl -s  http://download.mosek.com/$STATE/$MAJORVER/version)
MSKSHORTVER=$(echo $MOSEKVER | sed 's/\([0-9]\+\.[0-9]\+\).[0-9]\+\.\([0-9]\+\)/\1.\2/g')
MSKMAJMINVER=$(echo $MOSEKVER | sed 's/\([0-9]\+\.[0-9]\+\).[0-9]\+\.\([0-9]\+\)/\1/g')
MSKREV=$(echo $MOSEKVER | sed 's/\([0-9]\+\.[0-9]\+\).[0-9]\+\.\([0-9]\+\)/\2/g')

# Current version of PIP package
PKGVER=$(grep '^Version:' PKG-INFO |sed 's/Version: \([0-9]\+\.[0-9]\+\)[ab.]\([0-9]\+\)/\1.\2/g')
PKGREV=$(grep '^Version:' PKG-INFO |sed 's/Version: \([0-9]\+\.[0-9]\+\)[ab.]\([0-9]\+\)/\2/g')

echo $MSKREV, $PKGREV
if (( $MSKREV > $PKGREV )); then
    case "$STATE" in
        alpha) NEWPKGVER="${MSKMAJMINVER}a$MSKREV" ;;
        beta) NEWPKGVER="${MSKMAJMINVER}b$MSKREV" ;;
        *) NEWPKGVER="${MSKMAJMINVER}.$MSKREV" ;;
    esac
    
    mv PKG-INFO PKG-INFO.backup && \
    sed "s/^Version: .*/Version: $NEWPKGVER/g" < PKG-INFO.backup > PKG-INFO && \
    rm PKG-INFO.backup && \
    git add PKG-INFO && \
    git commit -m "update version to $NEWPKGVER" && \
    git tag "v$NEWPKGVER" && \
    git push origin refs/tags/"v$NEWPKGVER" || exit 1
else
    echo Package version is already up-to-date
fi

