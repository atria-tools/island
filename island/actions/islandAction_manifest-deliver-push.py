"""Action script for manifest-deliver-push.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

from death.ArgElement import ArgElement
from death.Arguments import Arguments

from island import (
    deliver,
    env,
)
from island.actions.islandAction_deliver import load_manifest, parse_options


def help() -> str:
    return "Push the delivery of the manifest (release branch, develop branch and tag) on the server"


def add_specific_arguments(my_args: Arguments, section: str) -> None:
    pass


def execute(_arguments: list[ArgElement]) -> int | None:
    parse_options(_arguments, ())
    configuration, mani = load_manifest()
    branches = [mani.deliver_master, mani.deliver_develop]
    if deliver.push_projects([configuration.get_manifest_config()], branches, action="manifest-deliver-push"):
        return env.ret_action_fail
    return None
