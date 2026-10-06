#!/usr/bin/python
"""Toolbox.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import fnmatch
import os
import time

# Local import
from realog import debug

from . import env


def get_current_path(file) -> str:
    return os.path.dirname(os.path.realpath(file))


def create_directory(path):
    os.makedirs(path, exist_ok=True)


def create_directory_of_file(file):
    path = os.path.dirname(file)
    create_directory(path)


def get_list_sub_path(path):
    # TODO : os.listdir(path)
    for _dirname, dirnames, _filenames in os.walk(path):
        return dirnames
    return []


def get_list_sub_files(path):
    # TODO : os.listdir(path)
    for _dirname, _dirnames, filenames in os.walk(path):
        return filenames
    return []


def file_read_data(path, binary=False):
    if not os.path.isfile(path):
        return ""
    with open(path, "rb" if binary is True else "r") as file:
        return file.read()


def version_to_string(version):
    version_ID = ""
    for id in version:
        if len(version_ID) != 0:
            if isinstance(id, str):
                version_ID += "-"
            else:
                version_ID += "."
        version_ID += str(id)
    return version_ID


def version_string_to_list(version):
    debug.verbose("parse version string '" + version + "'")
    if version == "":
        return [0, 0, 0]
    elems = version.split("-")
    if len(elems[0].split(".")) <= 1:
        debug.error("Can not parde a version with wrong version model '" + version + "'")
    out = [int(elem) for elem in elems[0].split(".")]
    if len(elems) >= 2:
        out.append(elems[1])
    return out


#
# @brief Write data in a specific path.
# @param[in] path Path of the data might be written.
# @param[in] data Data To write in the file.
# @param[in] only_if_new (default: False) Write data only if data is different.
# @return True Something has been copied
# @return False Nothing has been copied
#
def file_write_data(path, data: str, only_if_new: bool = False):
    if only_if_new is True and os.path.exists(path) is True:
        old_data = file_read_data(path)
        if old_data == data:
            return False
    # real write of data:
    create_directory_of_file(path)
    with open(path, "w") as file:
        file.write(data)
    return True


def get_list_base_display(id, count, elem):
    if env.get_display_folder_instead_of_git_name() is False:
        return f"{id}/{count} : {elem.name}"
    return f"{id}/{count} : {elem.path}"


is_first_time_sleep = True


def wait_for_server_if_needed():
    global is_first_time_sleep
    if is_first_time_sleep is False:
        is_first_time_sleep = True
        return
    if env.get_wait_between_sever_command() != 0:
        debug.info(f"Wait for server contrition ({env.get_wait_between_sever_command()} s)")
        time.sleep(env.get_wait_between_sever_command())


def filter_name_and_file(root, list_files, filter):
    # filter elements:
    tmp_list = fnmatch.filter(list_files, filter)
    return [elem for elem in tmp_list if os.path.isfile(os.path.join(root, elem)) is True]


def import_path_local(path, limit_sub_folder=1, exclude_path=(), base_name="*"):
    out = []
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
