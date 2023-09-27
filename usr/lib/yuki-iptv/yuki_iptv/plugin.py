#
# Copyright (c) 2023 Ame-chan-angel <amechanangel@proton.me>
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
import os.path
import sys
import logging
import importlib
import multiprocessing
from pathlib import Path
from yuki_iptv.log import args1

logger = logging.getLogger(__name__)


def init_plugins():
    if not args1.disable_plugins:
        plugins_dir = Path(os.path.abspath(os.path.dirname(__file__)), "plugins")
        if os.path.isdir(plugins_dir):
            sys.path.append(os.path.abspath(os.path.dirname(__file__)))
            for plugin in os.listdir(plugins_dir):
                if (
                    os.path.isfile(Path(plugins_dir, plugin))
                    and plugin.endswith(".py")
                    and not plugin.startswith("_")
                ):
                    module = importlib.import_module(
                        "plugins." + plugin.replace(".py", "")
                    )
                    if "init_plugin" in module.__dict__:
                        if (
                            multiprocessing.current_process().name == "MainProcess"
                            and "--multiprocessing-fork" not in sys.argv
                        ):
                            logger.info(f"Loading plugin {plugin.replace('.py', '')}")
                        module.init_plugin()
            sys.path.remove(os.path.abspath(os.path.dirname(__file__)))
    else:
        logger.info("Plugins disabled")
