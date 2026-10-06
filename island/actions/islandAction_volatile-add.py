"""Action script for volatile-add.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

from realog import debug

from island import (
    config,
    env,
    manifest,
)


def help():
    return "Add a 'volatile' repository with a local path (this element is update as an element in the manifest but is not managed by the manifest)"


def add_specific_arguments(my_args, section):
    my_args.add_arg("git repository", optionnal=False, desc="Git repositoty to download")
    my_args.add_arg("path", optionnal=False, desc="Path to install the new git repository")


def help_example():
    return "island volatile-add https://git.heeroyui.org/atria-tools/island.git git"


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
    manifest.check_island_is_init()

    # Update the current configuration:
    conf = config.get_unique_config()
    # TODO: Check if the local path does not exist in the manifest

    if conf.add_volatile(address_git, path) is False:
        return env.ret_action_executing_system_error
    conf.store()
    return None
