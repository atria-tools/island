"""Action script for manifest-checkout.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

from death.ArgElement import ArgElement
from death.Arguments import Arguments
from realog import debug

from island import (
    config,
    env,
    manifest,
    tools,
)
from island.actions import status


def help() -> str:
    return "Manifest Ckeckout a specific branch of repository"


def add_specific_arguments(my_args: Arguments, section: str) -> None:
    my_args.add("r", "remote", haveParam=True, desc="Name of the remote server")
    my_args.add_arg(
        "branch",
        optionnal=False,
        desc="Branch to checkout (if '__TAG__' ==> checkout specific repository tags)",
    )


def execute(_arguments: list[ArgElement]) -> int | None:
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
    manifest.check_island_is_init()

    configuration = config.get_unique_config()

    elem = configuration.get_manifest_config()
    base_display = tools.get_list_base_display(0, 0, elem)
    if status.checkout_elem(elem, argument_remote_name, branch_to_checkout, base_display) is False:
        return env.ret_action_fail
    return None
