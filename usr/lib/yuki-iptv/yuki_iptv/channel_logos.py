#
# Copyright (c) 2021, 2022 Astroncia <kestraly@gmail.com>
# Copyright (c) 2023, 2024 Ame-chan-angel <amechanangel@proton.me>
#
# This file is part of yuki-iptv.
#
# yuki-iptv is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# yuki-iptv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with yuki-iptv. If not, see <https://www.gnu.org/licenses/>.
#
# The Font Awesome pictograms are licensed under the CC BY 4.0 License.
# https://fontawesome.com/
# https://creativecommons.org/licenses/by/4.0/
#
import os

# import logging
# import traceback
import io
import base64
import hashlib
from pathlib import Path
from yuki_iptv.crossplatform import LOCAL_DIR
from yuki_iptv.requests_timeout import requests_get

# logger = logging.getLogger(__name__)

try:
    from wand.image import Image

    use_wand = True
except Exception:
    from PIL import Image

    use_wand = False


def fetch_remote_channel_icon(chan_name, logo_url, req_data_ua, req_data_ref):
    icon_ret = None
    if not logo_url:
        return None
    base64_enc = base64.b64encode(bytes(logo_url, "utf-8")).decode("utf-8")
    sha512_hash = str(hashlib.sha512(bytes(base64_enc, "utf-8")).hexdigest()) + ".png"
    cache_file = str(Path(LOCAL_DIR, "logo_cache", sha512_hash))
    if os.path.isfile(cache_file):
        # logger.debug("is remote icon, cache available")
        icon_ret = cache_file
    else:
        try:
            if os.path.isfile(logo_url.strip()):
                # logger.debug("is local icon")
                icon_ret = logo_url.strip()
            else:
                # logger.debug(
                #     "is remote icon, cache not available, fetching it..."
                # )
                req_data_headers = {"User-Agent": req_data_ua}
                if req_data_ref:
                    req_data_headers["Referer"] = req_data_ref
                req_data1 = requests_get(
                    logo_url,
                    headers=req_data_headers,
                    timeout=(3, 3),
                    stream=True,
                ).content
                if req_data1:
                    with io.BytesIO(req_data1) as im_logo_bytes:
                        if use_wand:
                            with Image(file=im_logo_bytes) as original:
                                with original.convert("png") as im_logo:
                                    im_logo.resize(64, 64)
                                    im_logo.save(filename=cache_file)
                                icon_ret = cache_file
                        else:
                            with Image.open(im_logo_bytes) as im_logo:
                                im_logo.thumbnail((64, 64))
                                im_logo.save(cache_file, "PNG")
                                icon_ret = cache_file
        except Exception:
            icon_ret = None
    return icon_ret


def channel_logos_worker(requested_logos, update_dict, append=""):
    # logger.debug("channel_logos_worker started")
    update_dict[f"logos{append}_inprogress"] = True
    for logo_channel in requested_logos:
        # logger.debug(f"Downloading logo for channel '{logo_channel}'...")
        logo_m3u = fetch_remote_channel_icon(
            logo_channel,
            requested_logos[logo_channel][0],
            requested_logos[logo_channel][2],
            requested_logos[logo_channel][3],
        )
        logo_epg = fetch_remote_channel_icon(
            logo_channel,
            requested_logos[logo_channel][1],
            requested_logos[logo_channel][2],
            requested_logos[logo_channel][3],
        )
        update_dict[f"LOGO{append}:::{logo_channel}"] = [logo_m3u, logo_epg]
    # logger.debug("channel_logos_worker ended")
    update_dict[f"logos{append}_inprogress"] = False
    update_dict[f"logos{append}_completed"] = True
