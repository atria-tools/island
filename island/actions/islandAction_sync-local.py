# -*- coding: utf-8 -*-
"""Action script for sync-local.

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
    return "Update all the branche to the trackin branch in local (no remote access)"


#
# @brief Add argument to the specific action
# @param[in,out] my_args (death.Arguments) Argument manager
# @param[in] section Name of the currect action
#
def add_specific_arguments(my_args, section):
    my_args.add(
        "r",
        "reset",
        haveParam=False,
        desc="Rebase the repository instead of 'reset --hard'",
    )


#
# @brief Execute the action required.
#
# @return error value [0 .. 50] the <0 value is reserved system ==> else, what you want.
#         None : No error (return program out 0)
#         -5  : env.ret_manifest_is_not_existing      : Manifest does not exit
#         -10 : env.ret_action_is_not_existing        : ACTION is not existing
#         -11 : env.ret_action_executing_system_error : ACTION execution system error
#         -12 : env.ret_action_wrong_parameters       : ACTION Wrong parameters
#         -13 : env.ret_action_partial_done           : ACTION partially done
#
def execute(_arguments):
    reset_instead_of_rebase = False
    for elem in _arguments:
        if elem.get_option_name() == "rebase":
            reset_instead_of_rebase = True
            debug.info("==> Request reset instead of rebase")
        else:
            debug.error(
                "SYNC Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'",
                ret_value=env.ret_action_wrong_parameters,
            )

    # check system is OK
    manifest.check_island_is_init()

    configuration = config.get_unique_config()

    debug.info("update manifest : '" + str(env.get_island_path_manifest()) + "'")
    is_modify_manifest = commands.check_repository_is_modify(env.get_island_path_manifest())
    if is_modify_manifest is True:
        debug.warning("Manifest is modify")
    else:
        ret_track = commands.get_current_tracking_branch(env.get_island_path_manifest())
        is_forward = commands.is_forward(env.get_island_path_manifest(), ret_track)
        if is_forward is True:
            # fetch the repository
            debug.warning(
                "sync-local: Not update ==> the MANIFEST is forward the remote branch "
                + str(commands.get_forward(env.get_island_path_manifest(), ret_track))
            )
        else:
            debug.verbose("Check behind:")
            is_behind = commands.is_behind(env.get_island_path_manifest(), ret_track)
            if is_behind is False:
                # fetch the repository
                debug.info("sync-local: MANIFEST is up-to-date")
            else:
                if reset_instead_of_rebase is True:
                    debug.info("sync-local: MANIFEST Reset to " + ret_track)
                    commands.reset_hard(env.get_island_path_manifest(), ret_track)
                else:
                    debug.info("sync-local: MANIFEST Rebase to " + ret_track)
                    commands.rebase(env.get_island_path_manifest(), ret_track)

    file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
    if os.path.exists(file_source_manifest) is False:
        debug.error(
            "Missing manifest file : '" + str(file_source_manifest) + "'",
            ret_value=env.ret_manifest_is_not_existing,
        )

    mani = manifest.Manifest(file_source_manifest)

    all_project = mani.get_all_configs()
    debug.info("synchronize : " + str(len(all_project)) + " projects")
    id_element = 0
    count_error = 0
    for elem in all_project:
        id_element += 1
        base_display = tools.get_list_base_display(id_element, len(all_project), elem)
        debug.info("----------------------------------------------------------------")
        debug.info("sync-local: " + base_display)
        # debug.debug("elem : " + str(elem))
        git_repo_path = os.path.join(env.get_island_root_path(), elem.path)
        if os.path.exists(git_repo_path) is False:
            # The Repository does not exist ==> Nothing to do...
            debug.warning("sync-local:    ==> Not download")
            count_error += 1
            continue

        if os.path.exists(os.path.join(git_repo_path, ".git")) is False:
            # path already exist but it is not used to as a git repo ==> this is an error
            debug.warning("sync-local: is already existing but not used for a git repository. Remove it and sync")
            count_error += 1
            continue

        # simply update the repository ...
        debug.verbose("Check modify:")
        is_modify = commands.check_repository_is_modify(git_repo_path)
        if is_modify is True:
            # fetch the repository
            debug.warning("sync-local: Not update ==> the repository is modified (pass through)")
            count_error += 1
            continue
        debug.verbose("Check tracking and local branch:")
        # get tracking branch
        ret_track = commands.get_current_tracking_branch(git_repo_path)
        select_branch = commands.get_current_branch(git_repo_path)
        debug.debug("sync-local: check: " + select_branch + " ==> " + ret_track)
        debug.verbose("Check forward:")
        is_forward = commands.is_forward(git_repo_path, ret_track)
        if is_forward is True:
            # fetch the repository
            debug.warning(
                "sync-local: Not update ==> the repository is forward the remote branch " + str(commands.get_forward(git_repo_path, ret_track))
            )
            count_error += 1
            continue
        debug.verbose("Check behind:")
        is_behind = commands.is_behind(git_repo_path, ret_track)
        if is_behind is False:
            # fetch the repository
            debug.info("sync-local: Nothing to do.")
            continue
        if reset_instead_of_rebase is True:
            debug.info("sync-local: Reset to " + ret_track)
            commands.reset_hard(git_repo_path, ret_track)
        else:
            debug.info("sync-local: Reset to " + ret_track)
            commands.rebase(git_repo_path, ret_track)
    if count_error != 0:
        debug.info("        ***********************************************************")
        debug.info("        **  local sync partial warning on " + str(count_error) + " repository")
        debug.info("        ***********************************************************")
        return env.ret_action_partial_done

    # Update the links:
    have_error = update_links.update(configuration, mani, "sync-local")
    if have_error is True:
        return -1
    return None
