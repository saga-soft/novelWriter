#!/bin/bash

if [ -z "$1" ]; then
  echo "Please provide the path to the novelWriter.AppImage file as an argument"
  exit 1
fi

if [ ! -e "$1" ]; then
  echo "File not found"
  exit 1
fi

IMGPATH="$(readlink -m "$1")"
echo "AppImage: $IMGPATH"

ICONPATH="$(dirname "$IMGPATH")/novelWriter.png"

if [ ! -e "$ICONPATH" ]; then
  echo "Downloading icon"
  wget https://raw.githubusercontent.com/saga-soft/novelWriter/main/setup/data/hicolor/256x256/apps/novelwriter.png -O "$ICONPATH"
fi

cat > $HOME/.local/share/applications/novelWriter.desktop <<EOF
[Desktop Entry]
Type=Application
Name=novelWriter
Comment=A plain text editor for planning and writing novels
Exec=${IMGPATH} %f
Icon=${ICONPATH}
Categories=Qt;Office;WordProcessor;
Terminal=false
EOF

update-desktop-database ~/.local/share/applications

echo "Desktop launcher generated"
