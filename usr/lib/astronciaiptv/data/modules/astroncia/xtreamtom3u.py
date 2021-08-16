class astroncia_data: # pylint: disable=too-few-public-methods
    pass

astroncia_data.m3u = '#EXTM3U\n'

def convert_xtream_to_m3u(data):
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
        astroncia_data.m3u += d + '\n' + url + '\n'
    return astroncia_data.m3u
