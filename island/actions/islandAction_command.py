"""Action script for command.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import os

from death.ArgElement import ArgElement
from realog import debug

from island import (
    config,
    env,
    manifest,
    multiprocess,
    tools,
)


def help() -> str:
    return "Write the command you want to be executed in every repository"


def have_unknow_argument() -> bool:
    return True


def execute(_arguments: list[ArgElement]) -> int | None:
    cmd = ""
    for elem in _arguments:
        debug.info("Get data element: " + str(elem.get_arg()))
        cmd += elem.get_arg() + " "

    # check system is OK
    manifest.check_island_is_init()

    configuration = config.get_unique_config()

    file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
    if os.path.exists(file_source_manifest) is False:
        debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")

    mani = manifest.Manifest(file_source_manifest)

    all_project = mani.get_all_configs()
    debug.info("status of: " + str(len(all_project)) + " projects")
    for id_element, elem in enumerate(all_project, start=1):
        debug.info("------------------------------------------")
        base_display = tools.get_list_base_display(id_element, len(all_project), elem)
        debug.info("execute command : " + base_display)
        tools.wait_for_server_if_needed()
        # debug.debug("elem : " + str(elem))
        git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
        if os.path.exists(git_repo_path) is False:
            debug.info("" + base_display + "\r\t\t\t\t\t\t\t\t\t" + "     (not download)")
            continue

        debug.verbose("execute : " + cmd)
        ret = multiprocess.run_command(cmd, cwd=git_repo_path)
        if ret[0] == 0:
            debug.info("ret=" + ret[1])
            debug.info("err=" + ret[2])
        else:
            debug.info("Execution ERROR")
    return None
