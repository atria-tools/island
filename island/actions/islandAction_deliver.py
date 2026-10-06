"""Action script for deliver.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import os

from death.ArgElement import ArgElement
from death.Arguments import Arguments
from realog import debug

from island import (
    config,
    deliver,
    env,
    manifest,
)


def help() -> str:
    return "Deliver the projects: release their develop branch on their release branch, with a new version"


def help_example() -> str:
    return "island deliver\nisland deliver --yes --bump=minor --push\nisland --filter=etk deliver"


def add_specific_arguments(my_args: Arguments, section: str) -> None:
    my_args.add("f", "from", haveParam=True, desc="Source branch to deliver (default: branch-develop of the manifest)")
    my_args.add("t", "to", haveParam=True, desc="Destination branch of the delivery (default: branch-release of the manifest)")
    my_args.add("y", "yes", desc="Deliver without asking")
    my_args.add("b", "bump", haveParam=True, desc="Step of every version: patch, minor or major (default: proposed from the commits)")
    my_args.add("p", "push", desc="Push the deliveries at the end (as deliver-push)")


def parse_options(arguments: list[ArgElement], names: tuple[str, ...]) -> dict[str, str]:
    """Read the options of a deliver action; a step of version must be patch, minor or major."""
    options: dict[str, str] = {}
    for elem in arguments:
        if elem.get_option_name() not in names:
            debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")
        options[elem.get_option_name()] = elem.get_arg()
    if "bump" in options and deliver.parse_bump(options["bump"]) is None:
        debug.error(f"Wrong step of version: '{options['bump']}', available: {', '.join(deliver.BUMPS)}", ret_value=env.ret_action_wrong_parameters)
    return options


def load_manifest() -> tuple[config.Config, manifest.Manifest]:
    manifest.check_island_is_init()
    configuration = config.get_unique_config()
    file_source_manifest = os.path.join(env.get_island_path_manifest(), configuration.get_manifest_name())
    if os.path.exists(file_source_manifest) is False:
        debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")
    return configuration, manifest.Manifest(file_source_manifest)


def execute(_arguments: list[ArgElement]) -> int | None:
    options = parse_options(_arguments, ("from", "to", "yes", "bump", "push"))
    _configuration, mani = load_manifest()
    source = options.get("from", mani.deliver_develop)
    destination = options.get("to", mani.deliver_master)

    all_project = mani.get_all_configs()
    plans, has_error = deliver.check_projects(all_project, source, destination)
    if has_error:
        print("Correct the errors above, or leave these projects out with --filter.")
        return env.ret_action_fail
    if len(plans) == 0:
        print("Nothing to deliver.")
        return None
    plans = deliver.confirm_plans(plans, deliver.parse_bump(options.get("bump")), "yes" in options)
    if len(plans) == 0:
        return None
    if deliver.deliver_plans(plans, mani.deliver_mode):
        return env.ret_action_fail
    if "push" not in options:
        print("Push them with: island deliver-push")
        return None
    if deliver.push_projects([plan.project for plan in plans], [destination, source]):
        return env.ret_action_fail
    return None
