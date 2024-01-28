# -*- coding: utf-8 -*-
"""Action script for manifest-status.

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
    return "Display status spécifically of the manifest"


#
# @brief Add argument to the specific action
# @param[in,out] my_args (death.Arguments) Argument manager
# @param[in] section Name of the currect action
#
def add_specific_arguments(_my_args, _section):
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
        if elem.get_option_name() == "tags":
            argument_display_tag = True
        else:
            debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    # check system is OK
    manifest.check_island_is_init()

    configuration = config.get_unique_config()
    elem = configuration.get_manifest_config()
    base_display = tools.get_list_base_display(0, 0, elem)
    ret = status.display_status(elem, argument_remote_name, argument_display_tag, 0, base_display)
    if ret != None:
        return env.ret_action_need_update
