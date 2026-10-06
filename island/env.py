"""Environment management.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import os

# Local import
from realog import debug


system_base_name = "island"


def set_system_base_name(val: str) -> None:
    global system_base_name
    system_base_name = val
    debug.debug("Set basename: '" + str(system_base_name) + "'")


def get_system_base_name() -> str:
    return system_base_name


def get_system_config_name() -> str:
    return system_base_name + "Config.py"


fetch_manifest = True


def set_fetch_manifest(val: bool) -> None:
    global fetch_manifest
    fetch_manifest = val


def get_fetch_manifest() -> bool:
    return fetch_manifest


wait_between_sever_command = 0


def set_wait_between_sever_command(val: int) -> None:
    global wait_between_sever_command
    wait_between_sever_command = val


def get_wait_between_sever_command() -> int:
    return wait_between_sever_command


filter_command = ""


def set_filter_command(val: str) -> None:
    global filter_command
    filter_command = val


def get_filter_command() -> str:
    return filter_command


def need_process_with_filter(data: str) -> bool:
    if filter_command == "":
        return True
    if len(data) < len(filter_command):
        return False
    return data[: len(filter_command)] == filter_command


display_folder_instead_of_git_name = True


def set_display_folder_instead_of_git_name(val: bool) -> None:
    global display_folder_instead_of_git_name
    display_folder_instead_of_git_name = val


def get_display_folder_instead_of_git_name() -> bool:
    return display_folder_instead_of_git_name


def _find_island_root_path() -> str:
    """Find the folder holding the ".island" folder: the current one or one of its 6 parents.

    :return: the folder found, else the current folder
    """
    for count_parent in range(7):
        path = os.path.join(os.getcwd(), *[".."] * count_parent)
        if os.path.exists(os.path.join(path, "." + get_system_base_name())):
            return path
    return os.getcwd()


island_root_path = _find_island_root_path()
island_path_user_config = os.path.join(island_root_path, get_system_config_name())
island_path = os.path.join(island_root_path, "." + get_system_base_name())
island_path_config = os.path.join(island_path, "config.json")
island_path_manifest = os.path.join(island_path, "manifest")


def get_island_root_path() -> str:
    """Get the parent path where is define ".island" folder.

    :return: the parent path of the ".island"
    """
    return island_root_path


def get_island_path() -> str:
    return island_path


def get_island_path_config() -> str:
    return island_path_config


def get_island_path_manifest() -> str:
    return island_path_manifest


def get_island_path_user_config() -> str:
    return island_path_user_config


ret_manifest_is_not_existing = -5
ret_action_is_not_existing = -10
ret_action_executing_system_error = -11
ret_action_wrong_parameters = -12
ret_action_partial_done = -13
ret_action_fail = -14

ret_action_need_update = 15
