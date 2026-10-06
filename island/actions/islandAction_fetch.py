"""Action script for fetch.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import os

from death.ArgElement import ArgElement
from death.Arguments import Arguments
from realog import debug

from island import (
    commands,
    config,
    env,
    manifest,
    tools,
)


def help() -> str:
    return "Fecth all the repository (get all modification on the server)"


def add_specific_arguments(my_args: Arguments, section: str) -> None:
    my_args.add("r", "remote", haveParam=True, desc="Name of the remote server")


def execute(_arguments: list[ArgElement]) -> int | None:
    argument_remote_name = ""
    for elem in _arguments:
        if elem.get_option_name() == "remote":
            debug.info("find remote name: '" + elem.get_arg() + "'")
            argument_remote_name = elem.get_arg()
        else:
            debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    # check system is OK
    manifest.check_island_is_init()

    debug.info("fetch manifest : '" + str(env.get_island_path_manifest()) + "'")
    commands.fetch(env.get_island_path_manifest(), "origin")

    configuration = config.get_unique_config()
    file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
    if os.path.exists(file_source_manifest) is False:
        debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")
    mani = manifest.Manifest(file_source_manifest)

    all_project = mani.get_all_configs()
    debug.info("fetch : " + str(len(all_project)) + " projects")
    for id_element, elem in enumerate(all_project, start=1):
        # configure remote name:
        if argument_remote_name == "":
            argument_remote_name = elem.select_remote["name"]

        base_display = tools.get_list_base_display(id_element, len(all_project), elem)
        debug.info("fetch: " + base_display)
        tools.wait_for_server_if_needed()
        # debug.debug("elem : " + str(elem))
        git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
        if os.path.exists(git_repo_path) is False:
            debug.error("can not fetch project that not exist")
            continue

        if os.path.exists(os.path.join(git_repo_path, ".git")) is False:
            # path already exist but it is not used to as a git repo ==> this is an error
            debug.error("path '" + git_repo_path + "' is already existing but not used for a git repository. Clean it and restart")

        # simply update the repository ...
        debug.verbose("Fetching project: ")

        commands.fetch(git_repo_path, argument_remote_name)
    return None
