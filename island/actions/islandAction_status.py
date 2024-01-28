# -*- coding: utf-8 -*-
"""Action script for status.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import os

from realog import debug
import status

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
    return "Get the status of all the repositories"


#
# @brief Add argument to the specific action
# @param[in,out] my_args (death.Arguments) Argument manager
# @param[in] section Name of the currect action
#
def add_specific_arguments(_my_args, _section):
    _my_args.add("r", "remote", haveParam=True, desc="Name of the remote server")
    _my_args.add(
        "t",
        "tags",
        haveParam=False,
        desc="Display if the commit is on a tag (and display it)",
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
    argument_remote_name = ""
    argument_display_tag = False
    for elem in _arguments:
        if elem.get_option_name() == "remote":
            debug.info("find remote name: '" + elem.get_arg() + "'")
            argument_remote_name = elem.get_arg()
        elif elem.get_option_name() == "tags":
            argument_display_tag = True
        else:
            debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    # check system is OK
    manifest.check_island_is_init()
    configuration = config.get_unique_config()

    file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
    if os.path.exists(file_source_manifest) is False:
        debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")

    mani = manifest.Manifest(file_source_manifest)
    is_modify_manifest = commands.check_repository_is_modify(env.get_island_path_manifest())
    if is_modify_manifest is True:
        debug.info("!!!!!!!!!!!! MANIFEST is modify !!!!!!!!")

    all_project = mani.get_all_configs()
    debug.info("status of: " + str(len(all_project)) + " projects")
    id_element = 0

    elem = configuration.get_manifest_config()
    base_display = tools.get_list_base_display(id_element, len(all_project), elem)
    status.display_status(elem, argument_remote_name, argument_display_tag, id_element, base_display)

    is_behind = False
    for elem in all_project:
        id_element += 1
        base_display = tools.get_list_base_display(id_element, len(all_project), elem)
        ret = status.display_status(elem, argument_remote_name, argument_display_tag, id_element, base_display)
        if ret != None:
            is_behind = True

    if is_behind is True:
        return env.ret_action_need_update
