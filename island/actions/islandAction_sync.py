# -*- coding: utf-8 -*-
"""Action script for sync.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import os

from realog import debug
import update_links

from island import (
    commands,
    config,
    env,
    manifest,
    multiprocess,
    tools,
)


#
# @brief Get the global description of the current action
# @return (string) the description string (fist line if reserved for the overview, all is for the specific display)
#
def help():
    return "Syncronize all the repository referenced"


#
# @brief at the end of the help wa have the example section
# @return (string) the Example description string
#
def help_example():
    return "island init https://git.heeroyui.org/atria-tools/island.git"


#
# @brief Add argument to the specific action
# @param[in,out] my_args (death.Arguments) Argument manager
# @param[in] section Name of the currect action
#
def add_specific_arguments(my_args, section):
    my_args.add(
        "d",
        "download",
        haveParam=False,
        desc="Just download the 'not download' repository",
    )


#
# @brief Execute the action required.
#
# @return error value [0 .. 50] the <0 value is reserved system ==> else, what you want.
#         None : No error (return program out 0)
#         -10 : ACTION is not existing
#         -11 : ACTION execution system error
#         -12 : ACTION Wrong parameters
#
def execute(_arguments):
    just_download = False
    for elem in _arguments:
        if elem.get_option_name() == "download":
            just_download = True
            debug.info("find remote name: '" + elem.get_arg() + "'")
        else:
            debug.error("SYNC Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    # check system is OK
    manifest.check_lutin_is_init()

    configuration = config.get_unique_config()

    # TODO: Load Old manifect to check diff ...

    debug.info("update manifest : '" + str(env.get_island_path_manifest()) + "'")
    is_modify_manifest = commands.check_repository_is_modify(env.get_island_path_manifest())
    if is_modify_manifest is True:
        commands.fetch(env.get_island_path_manifest(), "origin")
    else:
        commands.pull(env.get_island_path_manifest(), "origin")

    file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
    if os.path.exists(file_source_manifest) is False:
        debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")

    mani = manifest.Manifest(file_source_manifest)

    all_project = mani.get_all_configs()
    debug.info("synchronize : " + str(len(all_project)) + " projects")
    id_element = 0
    for elem in all_project:
        id_element += 1
        base_display = tools.get_list_base_display(id_element, len(all_project), elem)
        debug.info("sync : " + base_display)
        tools.wait_for_server_if_needed()
        # debug.debug("elem : " + str(elem))
        git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
        if elem.tag != None:
            debug.warning("Need to select a specific tag version ... " + elem.tag)
        if os.path.exists(git_repo_path) is False:
            # this is a new clone ==> this is easy ...
            # clone the manifest repository
            address_manifest = ""
            # example git@git.plouf.com:basic_folder
            address_manifest = elem.select_remote["fetch"]
            if elem.select_remote["fetch"][0:4] == "git@" and len(elem.select_remote["fetch"][4:].split(":")) <= 1:
                address_manifest += ":"
            else:
                address_manifest += "/"
            address_manifest += elem.name
            debug.info("clone the repo")
            ret = commands.clone(
                git_repo_path,
                address_manifest,
                branch_name=elem.branch,
                origin=elem.select_remote["name"],
            )
            if ret[0] != "" and ret[0] != False:
                # all is good, ready to get the system work corectly
                debug.info("'" + str(ret) + "'")
                debug.error("Clone repository does not work ... ")
                continue
            # add global mirror list
            for mirror in elem.select_remote["mirror"]:
                debug.verbose("Add global mirror: " + str(mirror))
                cmd = "git remote add " + mirror["name"] + " " + mirror["fetch"]
                if mirror["fetch"][0:4] == "git@":
                    cmd += ":"
                else:
                    cmd += "/"
                cmd += elem.name
                ret = multiprocess.run_command_direct(cmd, cwd=git_repo_path)
                if ret != "" and ret != False:
                    # all is good, ready to get the system work corectly
                    debug.info("'" + str(ret) + "'")
                    debug.warning("Can not add global mirror ... ")
                    continue
                debug.verbose("Add global mirror: " + str(mirror) + " (done)")
            # debug.info("plop " + str(elem.select_remote.keys()))
            # check submodule if requested:
            if elem.select_remote["sync"] is True and os.path.exists(os.path.join(git_repo_path, ".gitmodules")) is True:
                debug.info("    ==> update submodule")
                cmd = "git submodule init"
                ret = multiprocess.run_command_direct(cmd, cwd=git_repo_path)
                if ret != "" and ret != False:
                    # all is good, ready to get the system work corectly
                    debug.info("'" + str(ret) + "'")
                    debug.error("Can not init submodules ... ")
                    continue
                cmd = "git submodule update"
                ret = multiprocess.run_command_direct(cmd, cwd=git_repo_path)
                if ret[:16] == "Submodule path '":
                    # all is good ...
                    debug.info("    " + ret)
                elif ret != "" and ret != False:
                    # all is good, ready to get the system work corectly
                    debug.info("'" + str(ret) + "'")
                    debug.error("Can not init submodules ... ")
                    continue
            continue

        if just_download is True:
            debug.info("SYNC: Already downloaded")
            continue

        if os.path.exists(os.path.join(git_repo_path, ".git")) is False:
            # path already exist but it is not used to as a git repo ==> this is an error
            debug.error("path '" + git_repo_path + "' is already existing but not used for a git repository. Clean it and restart")

        # simply update the repository ...
        debug.verbose("Fetching project: ")

        # get tracking branch
        ret_track = commands.get_current_tracking_branch(git_repo_path)
        is_modify = commands.check_repository_is_modify(git_repo_path)
        select_branch = commands.get_current_branch(git_repo_path)

        if is_modify is True:
            # fetch the repository
            commands.fetch(git_repo_path, elem.select_remote["name"])
            debug.warning("[" + elem.name + "] Not update ==> the repository is modified (just fetch)")
            continue
        commands.pull(git_repo_path, elem.select_remote["name"])

        debug.verbose("select branch = '" + select_branch + "' track: '" + str(ret_track) + "'")
        # check submodule if requested:
        if elem.select_remote["sync"] is True and os.path.exists(os.path.join(git_repo_path, ".gitmodules")) is True:
            debug.info("    ==> sync submodule")
            commands.submodule_sync(git_repo_path, elem.select_remote["name"])

    # Update the links:
    have_error = update_links.update(configuration, mani, "sync-local")
    if have_error is True:
        return -1
    return None
