#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Toolbox.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import fnmatch
import os
import shutil
import time

# Local import
from realog import debug

from . import env


def get_run_path() -> str:
    return os.getcwd()


def get_current_path(file) -> str:
    return os.path.dirname(os.path.realpath(file))


def create_directory(path):
    try:
        os.stat(path)
    except:
        os.makedirs(path)


def create_directory_of_file(file):
    path = os.path.dirname(file)
    create_directory(path)


def get_list_sub_path(path):
    # TODO : os.listdir(path)
    for dirname, dirnames, filenames in os.walk(path):
        return dirnames
    return []


def get_list_sub_files(path):
    # TODO : os.listdir(path)
    for dirname, dirnames, filenames in os.walk(path):
        return filenames
    return []


def remove_path_and_sub_path(path):
    if os.path.isdir(path):
        debug.verbose("remove path : '" + path + "'")
        shutil.rmtree(path)


def remove_file(path):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.islink(path):
        os.remove(path)


def file_size(path):
    if not os.path.isfile(path):
        return 0
    statinfo = os.stat(path)
    return statinfo.st_size


def file_read_data(path, binary=False):
    if not os.path.isfile(path):
        return ""
    if binary is True:
        file = open(path, "rb")
    else:
        file = open(path, "r")
    data_file = file.read()
    file.close()
    return data_file


def version_to_string(version):
    version_ID = ""
    for id in version:
        if len(version_ID) != 0:
            if type(id) == str:
                version_ID += "-"
            else:
                version_ID += "."
        version_ID += str(id)
    return version_ID


def version_string_to_list(version):
    debug.verbose("parse version string '" + version + "'")
    out = []
    if version == "":
        return [0, 0, 0]
    elems = version.split("-")
    if len(elems[0].split(".")) <= 1:
        debug.error("Can not parde a version with wrong version model '" + version + "'")
    for elem in elems[0].split("."):
        out.append(int(elem))
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
    if only_if_new is True:
        if os.path.exists(path) is True:
            old_data = file_read_data(path)
            if old_data == data:
                return False
    # real write of data:
    create_directory_of_file(path)
    with open(path, "w") as file:
        file.write(data)
    return True


def list_to_str(list):
    if isinstance(list, str):
        return list + " "
    else:
        result = ""
        # mulyiple imput in the list ...
        for elem in list:
            result += list_to_str(elem)
        return result


def add_prefix(prefix, list):
    if list is None:
        return ""
    if isinstance(list, str):
        return prefix + list
    else:
        if len(list) == 0:
            return ""
        else:
            result = []
            for elem in list:
                result.append(prefix + elem)
            return result


def store_command(cmd_line, file):
    # write cmd line only after to prevent errors ...
    if file == "" or file is None:
        return
    debug.verbose("create cmd file: " + file)
    # Create directory:
    create_directory_of_file(file)
    # Store the command Line:
    file2 = open(file, "w")
    file2.write(cmd_line)
    file2.flush()
    file2.close()


def get_type_string(in_type):
    if type(in_type) == str:
        return "string"
    elif type(in_type) == list:
        return "list"
    elif type(in_type) == dict:
        return "dict"
    return "unknown"


# List tools:
def list_append_and_check(listout, newElement, order):
    for element in listout:
        if element == newElement:
            return
    listout.append(newElement)
    if order is True and not isinstance(newElement, dict):
        listout.sort()


def list_append_to(out_list, in_list, order=False):
    if type(in_list) == str:
        list_append_and_check(out_list, in_list, order)
    elif type(in_list) == list:
        # multiple input in the list ...
        for elem in in_list:
            list_append_and_check(out_list, elem, order)
    elif type(in_list) == dict:
        list_append_and_check(out_list, in_list, order)
    else:
        debug.warning(f"can not add in list other than {list/dict/str} : {type(in_list)}")


def list_append_to_2(listout, module, in_list, order=False):
    # sepcial cse of bool
    if type(in_list) == bool:
        listout[module] = in_list
        return
    # add list in the Map
    if module not in listout:
        listout[module] = []
    # add elements...
    list_append_to(listout[module], in_list, order)


#
# @brief The version number can be set in an external file to permit to have a singe position to change when create a vew version
# @param[in] path_module (string) Path of the module position
# @param[in] filename_or_version (string or list) Path of the version or the real version lint parameter
# @return (list) List of version number
#
def get_version_from_file_or_direct(path_module, filename_or_version):
    # check case of iser set the version directly
    if type(filename_or_version) == list:
        return filename_or_version
    # this use a version file
    file_data = file_read_data(os.path.join(path_module, filename_or_version))
    if len(file_data) == 0:
        debug.warning("not enough data in the file version size=0 " + path_module + " / " + filename_or_version)
        return [0, 0, 0]
    lines = file_data.split("\n")
    if len(lines) != 1:
        debug.warning(
            f"More than one line in the file version ==> bas case use mode: 'XX', XX.YYY', 'XX.Y.ZZZ' or 'XX.Y-dev' : {path_module} / {filename_or_version}"
        )
        return [0, 0, 0]
    line = lines[0]
    debug.debug(f"Parse line: '{line}'")
    # check if we have "-dev"
    dev_mode = ""
    list_tiret = line.split("-")
    if len(list_tiret) > 2:
        debug.warning(f"more than one '-' in version file {filename_or_version} : '{list_tiret}' in '{path_module}'")
    if len(list_tiret) >= 2:
        dev_mode = list_tiret[1]
        line = list_tiret[0]
    out = []
    list_elem = line.split(".")
    for elem in list_elem:
        out.append(int(elem))
    if dev_mode != "":
        out.append(dev_mode)
    debug.debug(f"    ==> {out}")
    return out


#
# @brief Get the list of the authors from an input list or a file
# @param[in] path_module (string) Path of the module position
# @param[in] filename_or_version (string or list) Path of the author file or the real list of authors
# @return (list) List of authors
#
def get_maintainer_from_file_or_direct(path_module, filename_or_author):
    # check case of it is set the version directly
    if isinstance(filename_or_author, list):
        return filename_or_author
    # this use a version file
    file_data = file_read_data(os.path.join(path_module, filename_or_author))
    if len(file_data) == 0:
        debug.warning(f"not enough data in the file author size=0 {path_module}/{filename_or_author}")
        return []
    # One user by line and # for comment line
    out = []
    for elem in file_data.split("\n"):
        if len(elem) == 0:
            continue
        if elem[0] == "#":
            # comment ...
            continue
        out.append(elem)
    return out


def remove_element(data, to_remove):
    base_data = []
    for elem in data:
        if type(elem) == list:
            for elem2 in elem:
                base_data.append(elem2)
        else:
            base_data.append(elem)
    base_remove = []
    for elem in to_remove:
        if type(elem) == list:
            for elem2 in elem:
                base_remove.append(elem2)
        else:
            base_remove.append(elem)
    out = []
    for elem in base_data:
        if elem not in base_remove:
            out.append(elem)
    return out


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
    out = []
    for elem in tmp_list:
        if os.path.isfile(os.path.join(root, elem)) is True:
            out.append(elem)
    return out


def filter_name(list_files, filter):
    # filter elements:
    return fnmatch.filter(list_files, filter)


def exclude_list(list_elements, filter):
    out = []
    for elem in list_elements:
        if elem not in filter:
            out.append(elem)
    return out


def import_path_local(path, limit_sub_folder=1, exclude_path=[], base_name="*"):
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
            tmp_out = import_path_local(folder, limit_sub_folder - 1, exclude_path, base_name)
            # add all the elements:
            for elem in tmp_out:
                out.append(elem)
    return out
