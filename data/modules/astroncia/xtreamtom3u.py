m3u = '#EXTM3U\n'

def convert_xtream_to_m3u(data):
    global m3u
    for channel in data:
        name = channel.name
        group = channel.group_title if channel.group_title else ''
        logo = channel.logo if channel.logo else ''
        url = channel.url
        d = '#EXTINF:0'
        if logo:
            d += " tvg-logo=\"{}\"".format(logo)
        if group:
            d += " group-title=\"{}\"".format(group)
        d += ",{}".format(name)
        m3u += d + '\n' + url + '\n'
    return m3u
