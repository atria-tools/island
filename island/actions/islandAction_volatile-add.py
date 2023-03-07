# -*- coding: utf-8 -*-
"""Action script for volatile-add.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import os

from realog import debug

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
    return "Add a 'volatile' repository with a local path (this element is update as an element in the manifest but is not managed by the manifest)"


#
# @brief Add argument to the specific action
# @param[in,out] my_args (death.Arguments) Argument manager
# @param[in] section Name of the currect action
#
def add_specific_arguments(my_args, section):
    my_args.add_arg("git repository", optionnal=False, desc="Git repositoty to download")
    my_args.add_arg("path", optionnal=False, desc="Path to install the new git repository")


#
# @brief at the end of the help wa have the example section
# @return (string) the Example description string
#
def help_example():
    return "island volatile-add https://git.heeroyui.org/atria-tools/island.git git"


#
# @brief Execute the action required.
#
# @return error value [0 .. 50] the <0 value is reserved system ==> else, what you want.
#         None : No error (return program out 0)
#         -5   : env.ret_manifest_is_not_existing      : Manifest does not exit
#         -10  : env.ret_action_is_not_existing        : ACTION is not existing
#         -11  : env.ret_action_executing_system_error : ACTION execution system error
#         -12  : env.ret_action_wrong_parameters       : ACTION Wrong parameters
#         -13  : env.ret_action_partial_done           : ACTION partially done
#
def execute(_arguments):
    if len(_arguments) == 0:
        debug.error("Missing argument to execute the current action [git repository] [path]")

    # the configuration available:
    path = ""
    address_git = ""
    for elem in _arguments:
        if elem.get_option_name() == "git repository":
            address_git = elem.get_arg()
        elif elem.get_option_name() == "path":
            path = elem.get_arg()
        else:
            debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    if address_git == "":
        debug.error(
            "volatile-add: Missing git repository address",
            env.ret_action_wrong_parameters,
        )

    debug.info("Add 'volatile' repository: '" + address_git + "' path='" + path + "'")

    # check system is OK
    manifest.check_lutin_is_init()

    # Update the current configuration:
    conf = config.get_unique_config()
    # TODO: Check if the local path does not exist in the manifest

    if False == conf.add_volatile(address_git, path):
        return env.ret_action_executing_system_error
    conf.store()
    return None
