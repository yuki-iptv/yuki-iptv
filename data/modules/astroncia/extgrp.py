def parse_extgrp(t):
    print("EXTGRP parsing...")
    tlist = t
    name = '""'
    group = ""
    url = '""'
    logo = '""'
    result = ["#EXTM3U"]

    for x in range(1, len(tlist)-1):
        line = tlist[x]
        nextline = tlist[x+1]
        if "#EXTINF" in line and not "tvg-name-astroncia-iptv" in line:
            name = line.rpartition(",")[2]
            if 'group-title=' in line:
                group = line.rpartition('group-title="')[2].partition('"')[0]
            else:
                group = ""
            if 'tvg-logo=' in line:
                logo = line.rpartition('tvg-logo="')[2].partition('"')[0]
            else:
                logo = ""
            if 'tvg-name=' in line:
                tvgname = line.rpartition('tvg-name="')[2].partition('"')[0]
            else:
                tvgname = ""
            if not "EXTGRP" in nextline:
                url = nextline
            else:
                group = nextline.partition('#EXTGRP:')[2]
                url = tlist[x+2]
            result.append(f'#EXTINF:-1 tvg-name="{tvgname}" tvg-name-astroncia-iptv="{name}" group-title="{group}" tvg-logo="{logo}",{name}\n{url}')

    return '\n'.join(result).split('\n')
