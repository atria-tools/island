# -*- coding: utf-8 -*-
"""Action script for manifest-checkout.

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
    return "Manifest Ckeckout a specific branch of repository"


#
# @brief Add argument to the specific action
# @param[in,out] my_args (death.Arguments) Argument manager
# @param[in] section Name of the currect action
#
def add_specific_arguments(my_args, section):
    my_args.add("r", "remote", haveParam=True, desc="Name of the remote server")
    my_args.add_arg(
        "branch",
        optionnal=False,
        desc="Branch to checkout (if '__TAG__' ==> checkout specific repository tags)",
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
    branch_to_checkout = ""
    for elem in _arguments:
        if elem.get_option_name() == "remote":
            debug.info("find remote name: '" + elem.get_arg() + "'")
            argument_remote_name = elem.get_arg()
        elif elem.get_option_name() == "branch":
            branch_to_checkout = elem.get_arg()
        else:
            debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    # check system is OK
    manifest.check_lutin_is_init()

    configuration = config.get_unique_config()

    elem = configuration.get_manifest_config()
    base_display = tools.get_list_base_display(0, 0, elem)
    if status.checkout_elem(elem, argument_remote_name, branch_to_checkout, base_display) is False:
        return env.ret_action_fail
