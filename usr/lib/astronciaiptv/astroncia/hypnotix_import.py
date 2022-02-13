'''Import playlists from Hypnotix'''
# SPDX-License-Identifier: GPL-3.0-only
# pylint: disable=missing-function-docstring
import json
import subprocess
import traceback
from astroncia.time import print_with_time

def import_from_hypnotix():
    playlists_hypnotix = {}
    hypnotix_import_ok = True
    print_with_time("Fetching playlists from Hypnotix...")
    try: # pylint: disable=too-many-nested-blocks
        hypnotix_cmd = "dconf dump /org/x/hypnotix/ 2>/dev/null | grep" + \
            " '^providers=' | sed 's/^providers=/{\"hypnotix\": /g'" + \
            " | sed 's/$/}/g' | sed \"s/'/\\\"/g\""
        hypnotix_cmd_eval = subprocess.check_output(
            hypnotix_cmd, shell=True, text=True
        ).strip()
        if hypnotix_cmd_eval:
            hypnotix_cmd_eval = json.loads(hypnotix_cmd_eval)['hypnotix']
            print_with_time("Hypnotix JSON output: {}".format(hypnotix_cmd_eval))
            print_with_time("")
            for provider_2 in hypnotix_cmd_eval:
                provider_2 = provider_2.replace(':' * 9, '^' * 9).split(':::')
                provider_2[2] = provider_2[2].split('^' * 9)
                print_with_time("{}".format(provider_2))
                prov_name_2 = provider_2[0]
                prov_m3u_2 = provider_2[2][0]
                # XTream API parse
                if provider_2[1] == 'xtream':
                    prov_m3u_2 = "XTREAM::::::::::::::" + \
                    "{}::::::::::::::{}::::::::::::::{}".format(
                        provider_2[3], # username
                        provider_2[4], # password
                        provider_2[2][0] # url
                    )
                    prov_epg_2 = provider_2[5]
                else:
                    # Local or remote URL
                    prov_epg_2 = provider_2[2][1]
                    # Local
                    if provider_2[1] == 'local':
                        if provider_2[2][0].startswith('file://'):
                            provider_2[2][0] = provider_2[2][0].replace('file://', '')
                        prov_m3u_2 = provider_2[2][0]
                playlists_hypnotix[prov_name_2] = {
                    "m3u": prov_m3u_2,
                    "epg": prov_epg_2,
                    "epgoffset": 0
                }
    except: # pylint: disable=bare-except
        print_with_time("")
        print_with_time(traceback.format_exc())
        print_with_time("Failed fetching playlists from Hypnotix!")
        hypnotix_import_ok = False
    return playlists_hypnotix, hypnotix_import_ok
