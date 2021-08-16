#!/bin/sh
cd "$(dirname "$(readlink -f "$0")")" || exit 1
ver="$1"
if [ "$ver" = "" ]; then
echo No version specified
exit 1
fi
echo "Using version: ${ver}"
sed -i "s/APP_VERSION = '.*/APP_VERSION = '${ver}'/g" ./usr/lib/astronciaiptv/astroncia_iptv.py
echo '{"version": "'"${ver}"'"}' > version.txt
debchange --distribution unstable -M
git add . && git commit -m "${ver}"
