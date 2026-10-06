"""Action script for ssh-key.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

from death.ArgElement import ArgElement
from death.Arguments import Arguments
from realog import debug

from island import (
    commands,
    config,
    env,
    manifest,
)


def help() -> str:
    return "Select the ssh key used to access on the git servers (set in all the repository), without argument display the current one"


def add_specific_arguments(my_args: Arguments, section: str) -> None:
    my_args.add("r", "remove", haveParam=False, desc="Remove the ssh key (use the default one of the user)")
    my_args.add_arg("key", optionnal=True, desc="Path of the ssh private key")


def help_example() -> str:
    return "island ssh-key ~/.ssh/id_ed25519_other"


def execute(_arguments: list[ArgElement]) -> int | None:
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
