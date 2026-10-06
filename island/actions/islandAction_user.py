# -*- coding: utf-8 -*-
"""Action script for user.

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
    return "Select the git user name and email (set in all the repository), without argument display the current ones"


#
# @brief Add argument to the specific action
# @param[in,out] my_args (death.Arguments) Argument manager
# @param[in] section Name of the currect action
#
def add_specific_arguments(my_args, section):
    my_args.add("n", "name", haveParam=True, desc="Git user name")
    my_args.add("e", "email", haveParam=True, desc="Git user email")
    my_args.add("r", "remove", haveParam=False, desc="Remove the git user name and email (use the default ones of the user)")


#
# @brief at the end of the help wa have the example section
# @return (string) the Example description string
#
def help_example():
    return 'island user --name "My Name" --email my.name@example.com'


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
    user_name = ""
    user_email = ""
    remove = False
    for elem in _arguments:
        if elem.get_option_name() == "name":
            user_name = elem.get_arg()
        elif elem.get_option_name() == "email":
            user_email = elem.get_arg()
        elif elem.get_option_name() == "remove":
            remove = True
        else:
            debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    if remove is True and (user_name != "" or user_email != ""):
        debug.error("user: can not set a name or an email and remove them", ret_value=env.ret_action_wrong_parameters)

    # check system is OK
    manifest.check_island_is_init()

    conf = config.get_unique_config()
    if remove is False and user_name == "" and user_email == "":
        debug.info("user name:  '" + conf.get_user_name() + "'")
        debug.info("user email: '" + conf.get_user_email() + "'")
        return None

    previous_config = commands.get_repository_config(conf)
    if remove is True or user_name != "":
        conf.set_user_name(user_name)
    if remove is True or user_email != "":
        conf.set_user_email(user_email)
    conf.store()

    count = manifest.configure_all_repository(conf, previous_config)
    if remove is True:
        debug.info("Remove the git user in " + str(count) + " repository")
    else:
        debug.info("Set the git user '" + conf.get_user_name() + "' <" + conf.get_user_email() + "> in " + str(count) + " repository")
    return None
