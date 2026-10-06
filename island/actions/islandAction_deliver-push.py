"""Action script for deliver-push.

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
    return "Push the deliveries (release branch, develop branch and tags) on the server"


def add_specific_arguments(my_args: Arguments, section: str) -> None:
    my_args.add("r", "remote", haveParam=True, desc="Name of the remote server (default: the remote of each project)")
    my_args.add("f", "from", haveParam=True, desc="Source branch of the deliveries (default: branch-develop of the manifest)")
    my_args.add("t", "to", haveParam=True, desc="Destination branch of the deliveries (default: branch-release of the manifest)")


def execute(_arguments: list[ArgElement]) -> int | None:
    options = parse_options(_arguments, ("remote", "from", "to"))
    _configuration, mani = load_manifest()
    branches = [options.get("to", mani.deliver_master), options.get("from", mani.deliver_develop)]
    if deliver.push_projects(mani.get_all_configs(), branches, options.get("remote")):
        return env.ret_action_fail
    return None
