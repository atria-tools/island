"""Action script for commit.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import os

from death.ArgElement import ArgElement
from death.Arguments import Arguments
from realog import debug

from island import (
    config,
    env,
    manifest,
    multiprocess,
    tools,
)


def help() -> str:
    return "Commit in all repository"


def add_specific_arguments(my_args: Arguments, section: str) -> None:
    my_args.add("m", "message", haveParam=True, desc="Message to commit data")
    my_args.add("a", "all", desc="Commit all elements")
    my_args.add("", "amend", desc="Ammend data at the previous commit")


def execute(_arguments: list[ArgElement]) -> int | None:
    argument_message = ""
    argument_amend = ""
    argument_all = ""
    for elem in _arguments:
        if elem.get_option_name() == "message":
            debug.info("find message: '" + elem.get_arg() + "'")
            argument_message = ' --message "' + elem.get_arg() + '" '
        elif elem.get_option_name() == "all":
            argument_all = " --all "
        elif elem.get_option_name() == "amend":
            argument_amend = " --amend "
        else:
            debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    # check system is OK
    manifest.check_island_is_init()

    configuration = config.get_unique_config()

    file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
    if os.path.exists(file_source_manifest) is False:
        debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")
    mani = manifest.Manifest(file_source_manifest)

    all_project = mani.get_all_configs()
    debug.info("commit : " + str(len(all_project)) + " projects")
    for id_element, elem in enumerate(all_project, start=1):
        base_display = tools.get_list_base_display(id_element, len(all_project), elem)
        debug.info("commit: " + base_display)
        git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
        if os.path.exists(git_repo_path) is False:
            debug.error("can not commit project that not exist")
            continue

        if os.path.exists(os.path.join(git_repo_path, ".git")) is False:
            # path already exist but it is not used to as a git repo ==> this is an error
            debug.warning("path '" + git_repo_path + "' is already existing but not used for a git repository. Clean it and restart")
            continue

        # simply update the repository ...
        debug.verbose("commit in project:")
        # fetch the repository
        cmd = "git commit " + argument_amend + argument_all + argument_message
        debug.debug("execute : " + cmd)
        multiprocess.run_command_direct(cmd, cwd=git_repo_path)
    return None
