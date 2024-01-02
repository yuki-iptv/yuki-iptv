#
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
import time
import sys
import requests


# https://stackoverflow.com/questions/21965484/timeout-for-python-requests-get-entire-response/71453648#71453648


def requests_get(*args, **kwargs):
    def trace_func(frame, event, arg):
        if time.time() - start_time > 20:
            raise Exception("Timeout 20 seconds exceeded")

        return trace_func

    start_time = time.time()
    sys.settrace(trace_func)

    try:
        result = requests.get(*args, **kwargs)
    except Exception:
        raise
    finally:
        sys.settrace(None)
    return result
