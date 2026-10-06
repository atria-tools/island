"""Toolbox.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

from collections.abc import Sequence
import fnmatch
import os
import time
from typing import TYPE_CHECKING

# Local import
from realog import debug

from . import env


if TYPE_CHECKING:
    from .repo_config import RepoConfig


def get_current_path(file: str) -> str:
    return os.path.dirname(os.path.realpath(file))


def create_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def create_directory_of_file(file: str) -> None:
    path = os.path.dirname(file)
    create_directory(path)


def get_list_sub_path(path: str) -> list[str]:
    # TODO : os.listdir(path)
    for _dirname, dirnames, _filenames in os.walk(path):
        return dirnames
    return []


def get_list_sub_files(path: str) -> list[str]:
    # TODO : os.listdir(path)
    for _dirname, _dirnames, filenames in os.walk(path):
        return filenames
    return []


def file_read_data(path: str) -> str:
    if not os.path.isfile(path):
        return ""
    with open(path) as file:
        return file.read()


def version_to_string(version: Sequence[int | str]) -> str:
    version_id = ""
    for elem in version:
        if len(version_id) != 0:
            if isinstance(elem, str):
                version_id += "-"
            else:
                version_id += "."
        version_id += str(elem)
    return version_id


def version_string_to_list(version: str) -> list[int | str]:
    debug.verbose("parse version string '" + version + "'")
    if version == "":
        return [0, 0, 0]
    elems = version.split("-")
    if len(elems[0].split(".")) <= 1:
        debug.error("Can not parde a version with wrong version model '" + version + "'")
    out: list[int | str] = [int(elem) for elem in elems[0].split(".")]
    if len(elems) >= 2:
        out.append(elems[1])
    return out


def file_write_data(path: str, data: str, only_if_new: bool = False) -> bool:
    """Write data in a file.

    :param path: Path of the file
    :param data: Data to write in the file
    :param only_if_new: Write the data only when they differ from those of the file
    :return: True when the file was written
    """
    if only_if_new is True and os.path.exists(path) is True:
        old_data = file_read_data(path)
        if old_data == data:
            return False
    # real write of data:
    create_directory_of_file(path)
    with open(path, "w") as file:
        file.write(data)
    return True


def get_list_base_display(id_element: int, count: int, elem: "RepoConfig") -> str:
    if env.get_display_folder_instead_of_git_name() is False:
        return f"{id_element}/{count} : {elem.name}"
    return f"{id_element}/{count} : {elem.path}"


is_first_time_sleep = True


def wait_for_server_if_needed() -> None:
    global is_first_time_sleep
    if is_first_time_sleep is False:
        is_first_time_sleep = True
        return
    if env.get_wait_between_sever_command() != 0:
        debug.info(f"Wait for server contrition ({env.get_wait_between_sever_command()} s)")
        time.sleep(env.get_wait_between_sever_command())


def filter_name_and_file(root: str, list_files: list[str], pattern: str) -> list[str]:
    # filter elements:
    tmp_list = fnmatch.filter(list_files, pattern)
    return [elem for elem in tmp_list if os.path.isfile(os.path.join(root, elem)) is True]


def import_path_local(path: str, limit_sub_folder: int = 1, exclude_path: tuple[str, ...] | list[str] = (), base_name: str = "*") -> list[str]:
    out: list[str] = []
    debug.debug(f"island files: {path} [START] {limit_sub_folder}")
    if limit_sub_folder == 0:
        debug.verbose("Sub-parsing limitation append ...")
        return []
    list_files = get_list_sub_files(path)
    # filter elements:
    debug.debug(f"island files: {path} : {list_files}")
    tmp_list_island_file = filter_name_and_file(path, list_files, base_name)
    debug.debug(f"island files (filtered): {path} : {tmp_list_island_file}")
    # Import the module:
    for filename in tmp_list_island_file:
        out.append(os.path.join(path, filename))
        debug.debug(f"     Find a file : '{out[-1]}'")
    list_folders_full = get_list_sub_path(path)
    list_folders = []
    for elem in list_folders_full:
        if elem in exclude_path:
            debug.verbose(f"find '{elem}' in exclude_path={exclude_path}")
            continue
        list_folders.append(os.path.join(path, elem))
    # check if we need to parse sub_folder
    if len(list_folders) != 0:
        debug.debug(f"     Find a folder : {list_folders}")
        for folder in list_folders:
            out.extend(import_path_local(folder, limit_sub_folder - 1, exclude_path, base_name))
    return out
