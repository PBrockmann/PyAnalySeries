#!/bin/bash

# ./make_icns.sh resources/PyAnalySeries_icon.png file.icns

ICON_SRC=$1
ICNS_NAME=$2

TMP_DIR="tmp_icons"
mkdir -p $TMP_DIR

rm -rf $TMP_DIR/*.png

declare -A sizes=(
  [icon_16x16]=16
  [icon_32x32]=32
  [icon_128x128]=128
  [icon_256x256]=256
  [icon_512x512]=512
  [icon_1024x1024]=1024
)

for name in "${!sizes[@]}"; do
  size=${sizes[$name]}
  convert $ICON_SRC -resize ${size}x${size} $TMP_DIR/${name}.png
done

png2icns $ICNS_NAME $TMP_DIR/*.png

ls -l $ICNS_NAME
