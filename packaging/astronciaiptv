#!/bin/bash
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
env python3 -m astroncia_iptv
ret_code="$?"
if [ "$ret_code" = "0" ]; then
reset
fi
exit "$ret_code"
