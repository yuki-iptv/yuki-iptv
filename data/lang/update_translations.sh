#!/bin/sh
cd "$(dirname "$(readlink -f "$0")")" || exit 1
find . -type f -name '*.po' -exec bash -c 'msgfmt -o ${0/.po/.mo} $0' {} \;
