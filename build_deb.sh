#!/usr/bin/env bash
set -euo pipefail

VERSION=$(grep '^version' pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/')
PKG="memboard_${VERSION}_amd64"
DIST="dist/MemBoard"

if [ ! -d "$DIST" ]; then
    echo "Building PyInstaller bundle..."
    pyinstaller memboard.spec --clean --noconfirm
fi

echo "Assembling deb: $PKG..."
rm -rf "$PKG"
mkdir -p "$PKG/DEBIAN"
mkdir -p "$PKG/opt/memboard"
mkdir -p "$PKG/usr/share/applications"

cp -r "$DIST/." "$PKG/opt/memboard/"
cp memboard.desktop "$PKG/usr/share/applications/memboard.desktop"

INSTALLED_KB=$(du -sk "$PKG/opt" | cut -f1)

cat > "$PKG/DEBIAN/control" <<EOF
Package: memboard
Version: $VERSION
Architecture: amd64
Maintainer: hwasim6
Installed-Size: $INSTALLED_KB
Depends: libportaudio2
Section: games
Priority: optional
Description: Guitar fretboard memorization trainer
 MemBoard listens to your guitar through a microphone, shows you a note
 to find, and measures how fast and accurately you can locate it on the
 fretboard. Sessions are logged and personal bests are tracked.
EOF

dpkg-deb --build --root-owner-group "$PKG"
echo "Done: ${PKG}.deb"
