"""Action script for manifest-sync.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

from realog import debug

from island import (
    commands,
    env,
    manifest,
)


def help():
    return "Syncronize all the repository referenced"


def add_specific_arguments(my_args, section):
    pass


def execute(_arguments):
    for elem in _arguments:
        debug.error("pull Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    # check system is OK
    manifest.check_island_is_init()

    debug.info("update manifest : '" + str(env.get_island_path_manifest()) + "'")
    is_modify_manifest = commands.check_repository_is_modify(env.get_island_path_manifest())
    if is_modify_manifest is True:
        commands.fetch(env.get_island_path_manifest(), "origin")
    else:
        commands.pull(env.get_island_path_manifest(), "origin")
