"""Action script for manifest-deliver.

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import os

from death.ArgElement import ArgElement
from death.Arguments import Arguments

from island import (
    deliver,
    env,
    manifest,
)
from island.actions.islandAction_deliver import load_manifest, parse_options


def help() -> str:
    return "Deliver the manifest: release it with each project pinned on its last release"


def help_example() -> str:
    return "island deliver --push\nisland manifest-deliver --push"


def add_specific_arguments(my_args: Arguments, section: str) -> None:
    my_args.add("y", "yes", desc="Deliver without asking")
    my_args.add("b", "bump", haveParam=True, desc="Step of the version: patch, minor or major (default: proposed from the commits)")
    my_args.add("p", "push", desc="Push the delivery at the end (as manifest-deliver-push)")


def execute(_arguments: list[ArgElement]) -> int | None:
    options = parse_options(_arguments, ("yes", "bump", "push"))
    configuration, mani = load_manifest()
    source = mani.deliver_develop
    destination = mani.deliver_master

    pins, has_error = deliver.pin_projects(mani.get_all_configs(), destination)
    if has_error:
        print("Correct the errors above, or leave these projects out with --filter.")
        return env.ret_action_fail
    manifest_elem = configuration.get_manifest_config()
    changes = deliver.pin_changes(manifest_elem, destination, configuration.get_manifest_name(), pins)
    plans, has_error = deliver.check_projects([manifest_elem], source, destination, "manifest-check", changes)
    if has_error:
        return env.ret_action_fail
    if len(plans) == 0:
        print("Nothing to deliver: the manifest and its pins did not change.")
        return None
    plans = deliver.confirm_plans(plans, deliver.parse_bump(options.get("bump")), "yes" in options)
    if len(plans) == 0:
        return None

    def pin(path: str) -> None:
        manifest.tag_manifest(os.path.join(path, configuration.get_manifest_name()), pins)

    def unpin(path: str) -> None:
        manifest.tag_clear(os.path.join(path, configuration.get_manifest_name()))

    if deliver.deliver_plans(plans, mani.deliver_mode, "manifest-deliver", {id(manifest_elem): (pin, unpin)}):
        return env.ret_action_fail
    if "push" not in options:
        print("Push it with: island manifest-deliver-push")
        return None
    if deliver.push_projects([manifest_elem], [destination, source], action="manifest-deliver-push"):
        return env.ret_action_fail
    return None
