# -*- coding: utf-8 -*-
"""Action script for deliver-push.

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
    return "Push a delover (develop & master & tag) on the remotre server"


#
# @brief Add argument to the specific action
# @param[in,out] my_args (death.Arguments) Argument manager
# @param[in] section Name of the currect action
#
def add_specific_arguments(my_args, section):
    my_args.add("r", "remote", haveParam=True, desc="Name of the remote server")


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
    for elem in _arguments:
        if elem.get_option_name() == "remote":
            debug.info("find remote name: '" + elem.get_arg() + "'")
            argument_remote_name = elem.get_arg()
        else:
            debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    # check system is OK
    manifest.check_lutin_is_init()

    configuration = config.get_unique_config()

    file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
    if os.path.exists(file_source_manifest) is False:
        debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")
    mani = manifest.Manifest(file_source_manifest)

    destination_branch = mani.deliver_master
    source_branch = mani.deliver_develop

    all_project = mani.get_all_configs()
    debug.info("fetch : " + str(len(all_project)) + " projects")
    id_element = 0
    for elem in all_project:
        id_element += 1
        # configure remote name:
        if argument_remote_name == "":
            argument_remote_name = elem.select_remote["name"]
        base_display = tools.get_list_base_display(id_element, len(all_project), elem)
        debug.info("deliver-push: " + base_display)
        tools.wait_for_server_if_needed()
        status.deliver_push(elem, argument_remote_name, destination_branch, source_branch, base_display)
