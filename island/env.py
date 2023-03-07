#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Environment management.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import os

# Local import
from realog import debug


system_base_name = "island"


def set_system_base_name(val):
    global system_base_name
    system_base_name = val
    debug.debug("Set basename: '" + str(system_base_name) + "'")


def get_system_base_name():
    global system_base_name
    return system_base_name


def get_system_config_name():
    global system_base_name
    return system_base_name + "Config.py"


fetch_manifest = True


def set_fetch_manifest(val):
    global fetch_manifest
    fetch_manifest = val


def get_fetch_manifest():
    global fetch_manifest
    return fetch_manifest


wait_between_sever_command = 0


def set_wait_between_sever_command(val):
    global wait_between_sever_command
    wait_between_sever_command = val


def get_wait_between_sever_command():
    global wait_between_sever_command
    return wait_between_sever_command


filter_command = ""


def set_filter_command(val):
    global filter_command
    filter_command = val


def get_filter_command():
    global filter_command
    return filter_command


def need_process_with_filter(data):
    global filter_command
    if filter_command == "":
        return True
    if len(data) < len(filter_command):
        return False
    if data[: len(filter_command)] == filter_command:
        return True
    return False


display_folder_instead_of_git_name = True


def set_display_folder_instead_of_git_name(val):
    global display_folder_instead_of_git_name
    display_folder_instead_of_git_name = val


def get_display_folder_instead_of_git_name():
    global display_folder_instead_of_git_name
    return display_folder_instead_of_git_name


island_root_path = os.path.join(os.getcwd())
if os.path.exists(os.path.join(island_root_path, "." + get_system_base_name())) is True:
    # all is good ...
    pass
elif os.path.exists(os.path.join(island_root_path, "..", "." + get_system_base_name())):
    island_root_path = os.path.join(os.getcwd(), "..")
elif os.path.exists(os.path.join(island_root_path, "..", "..", "." + get_system_base_name())):
    island_root_path = os.path.join(os.getcwd(), "..", "..")
elif os.path.exists(os.path.join(island_root_path, "..", "..", "..", "." + get_system_base_name())):
    island_root_path = os.path.join(os.getcwd(), "..", "..", "..")
elif os.path.exists(os.path.join(island_root_path, "..", "..", "..", "..", "." + get_system_base_name())):
    island_root_path = os.path.join(os.getcwd(), "..", "..", "..", "..")
elif os.path.exists(os.path.join(island_root_path, "..", "..", "..", "..", "..", "." + get_system_base_name())):
    island_root_path = os.path.join(os.getcwd(), "..", "..", "..", "..", "..")
elif os.path.exists(
    os.path.join(
        island_root_path,
        "..",
        "..",
        "..",
        "..",
        "..",
        "..",
        "." + get_system_base_name(),
    )
):
    island_root_path = os.path.join(os.getcwd(), "..", "..", "..", "..", "..", "..")
else:
    # debug.error("the root path of " + get_system_base_name() + " must not be upper that 6 parent path")
    pass
island_path_user_config = os.path.join(island_root_path, get_system_config_name())
island_path = os.path.join(island_root_path, "." + get_system_base_name())
island_path_config = os.path.join(island_path, "config.json")
island_path_manifest = os.path.join(island_path, "manifest")


def get_island_root_path() -> str:
    """Get the parent path where is define ".island" folder.

    :return: the parent path of the ".island"
    """
    global island_root_path
    return island_root_path


def get_island_path() -> str:
    global island_path
    return island_path


def get_island_path_config() -> str:
    global island_path_config
    return island_path_config


def get_island_path_manifest() -> str:
    global island_path_manifest
    return island_path_manifest


def get_island_path_user_config() -> str:
    global island_path_user_config
    return island_path_user_config


ret_manifest_is_not_existing = -5
ret_action_is_not_existing = -10
ret_action_executing_system_error = -11
ret_action_wrong_parameters = -12
ret_action_partial_done = -13
ret_action_fail = -14

ret_action_need_update = 15
