"""Action script for volatile-list.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

from death.ArgElement import ArgElement
from realog import debug

from island import (
    config,
    manifest,
)


def help() -> str:
    return "List all the volatile repository"


def execute(_arguments: list[ArgElement]) -> int | None:
    for elem in _arguments:
        debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")

    # check system is OK
    manifest.check_island_is_init()

    conf = config.get_unique_config()
    volatiles = conf.get_volatile()
    debug.info("List of all volatiles repository: ")
    for elem in volatiles:
        debug.info("\t" + elem["path"] + "\r\t\t\t\t" + elem["git_address"])

    return None
