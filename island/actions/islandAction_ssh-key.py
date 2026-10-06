# -*- coding: utf-8 -*-
"""Action script for ssh-key.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

from realog import debug

from island import (
    commands,
    config,
    env,
    manifest,
)


#
# @brief Get the global description of the current action
# @return (string) the description string (fist line if reserved for the overview, all is for the specific display)
#
def help():
    return "Select the ssh key used to access on the git servers (set in all the repository), without argument display the current one"


#
# @brief Add argument to the specific action
# @param[in,out] my_args (death.Arguments) Argument manager
# @param[in] section Name of the currect action
#
def add_specific_arguments(my_args, section):
    my_args.add("r", "remove", haveParam=False, desc="Remove the ssh key (use the default one of the user)")
    my_args.add_arg("key", optionnal=True, desc="Path of the ssh private key")


#
# @brief at the end of the help wa have the example section
# @return (string) the Example description string
#
def help_example():
    return "island ssh-key ~/.ssh/id_ed25519_other"


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
    ssh_key = ""
    remove = False
    for elem in _arguments:
        if elem.get_option_name() == "key":
            ssh_key = commands.get_ssh_key_path(elem.get_arg())
        elif elem.get_option_name() == "remove":
            remove = True
        else:
            debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    if remove is True and ssh_key != "":
        debug.error("ssh-key: can not set a key and remove it", ret_value=env.ret_action_wrong_parameters)

    # check system is OK
    manifest.check_island_is_init()

    conf = config.get_unique_config()
    previous_ssh_key = conf.get_ssh_key()
    if remove is False and ssh_key == "":
        if previous_ssh_key == "":
            debug.info("No ssh key selected (use the default one of the user)")
        else:
            debug.info("ssh key: '" + previous_ssh_key + "'")
        return None

    previous_config = commands.get_repository_config(conf)
    conf.set_ssh_key(ssh_key)
    conf.store()

    count = manifest.configure_all_repository(conf, previous_config)
    if remove is True:
        debug.info("Remove the ssh key in " + str(count) + " repository")
    else:
        debug.info("Set the ssh key '" + ssh_key + "' in " + str(count) + " repository")
    return None
