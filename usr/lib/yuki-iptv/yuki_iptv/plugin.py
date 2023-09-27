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
import multiprocessing
import importlib
from pathlib import Path


def print_log(msg):
    if (
        multiprocessing.current_process().name == "MainProcess"
        and "--multiprocessing-fork" not in sys.argv
    ):
        print(msg)


def init_plugins():
    if "--disable-plugins" not in sys.argv:
        disabled_plugins = [
            x.replace("--disable-plugin=", "").split(",")
            for x in sys.argv
            if x.startswith("--disable-plugin=")
        ]
        if disabled_plugins:
            disabled_plugins = disabled_plugins[0]
        plugins_dir = Path(os.path.abspath(os.path.dirname(__file__)), "plugins")
        if os.path.isdir(plugins_dir):
            sys.path.append(os.path.abspath(os.path.dirname(__file__)))
            for plugin in os.listdir(plugins_dir):
                if (
                    os.path.isfile(Path(plugins_dir, plugin))
                    and plugin.endswith(".py")
                    and not plugin.startswith("_")
                ):
                    if plugin.replace(".py", "") not in disabled_plugins:
                        module = importlib.import_module(
                            "plugins." + plugin.replace(".py", "")
                        )
                        if "init_plugin" in module.__dict__:
                            print_log(f"Loading plugin: {plugin.replace('.py', '')}")
                            module.init_plugin()
                    else:
                        print_log(f"Plugin disabled: {plugin.replace('.py', '')}")
            sys.path.remove(os.path.abspath(os.path.dirname(__file__)))
    else:
        print_log("Plugins disabled")
