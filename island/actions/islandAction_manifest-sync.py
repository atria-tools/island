# -*- coding: utf-8 -*-
"""Action script for manifest-sync.

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
    return "Syncronize all the repository referenced"


#
# @brief Add argument to the specific action
# @param[in,out] my_args (death.Arguments) Argument manager
# @param[in] section Name of the currect action
#
def add_specific_arguments(my_args, section):
    pass


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
    for elem in _arguments:
        debug.error("pull Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    # check system is OK
    manifest.check_lutin_is_init()

    configuration = config.get_unique_config()

    debug.info("update manifest : '" + str(env.get_island_path_manifest()) + "'")
    is_modify_manifest = commands.check_repository_is_modify(env.get_island_path_manifest())
    if is_modify_manifest is True:
        commands.fetch(env.get_island_path_manifest(), "origin")
    else:
        commands.pull(env.get_island_path_manifest(), "origin")
