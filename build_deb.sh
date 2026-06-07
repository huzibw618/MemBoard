#!/usr/bin/env bash
set -euo pipefail

VERSION=$(grep '^version' pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/')
PKG="memboard_${VERSION}_amd64"
DIST="dist/MemBoard"

if [ ! -d "$DIST" ]; then
    echo "Building PyInstaller bundle..."
    uv run --extra build pyinstaller memboard.spec --clean --noconfirm
fi

echo "Assembling deb: $PKG..."
rm -rf "$PKG"
mkdir -p "$PKG/DEBIAN"
mkdir -p "$PKG/opt/memboard"
mkdir -p "$PKG/usr/share/applications"

cp -r "$DIST/." "$PKG/opt/memboard/"
cp memboard.desktop "$PKG/usr/share/applications/memboard.desktop"

python3 -c "
import os
from PIL import Image
img = Image.open('assets/icon.png')
for size in [16, 32, 48, 64, 128, 256]:
    d = '$PKG/usr/share/icons/hicolor/%dx%d/apps' % (size, size)
    os.makedirs(d, exist_ok=True)
    img.resize((size, size), Image.LANCZOS).save(d + '/memboard.png')
"

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

cat > "$PKG/DEBIAN/postinst" <<'EOF'
#!/bin/sh
gtk-update-icon-cache -f -t /usr/share/icons/hicolor/ 2>/dev/null || true
EOF
chmod 755 "$PKG/DEBIAN/postinst"

dpkg-deb --build --root-owner-group "$PKG"
echo "Done: ${PKG}.deb"
