# -*- coding: utf-8 -*-
"""Action script for volatile-list.

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
def help() -> str:
    return "List all the volatile repository"


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
    for elem in _arguments:
        debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    # check system is OK
    manifest.check_lutin_is_init()

    conf = config.get_unique_config()
    volatiles = conf.get_volatile()
    debug.info("List of all volatiles repository: ")
    for elem in volatiles:
        debug.info("\t" + elem["path"] + "\r\t\t\t\t" + elem["git_address"])

    return None
