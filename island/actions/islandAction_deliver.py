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
from island.parallel import Status


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
    my_args.add("u", "unreleased", desc="Deliver the projects never released too (by default only when a delivered project needs them)")


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
    options = parse_options(_arguments, ("from", "to", "yes", "bump", "push", "unreleased"))
    _configuration, mani = load_manifest()
    source = options.get("from", mani.deliver_develop)
    destination = options.get("to", mani.deliver_master)

    # every project is checked: one that --filter leaves out joins the delivery when a project delivered needs it
    selected = {elem.path for elem in mani.get_all_configs()}
    checked = deliver.check_all(mani.get_all_configs(use_filter=False), source, destination)
    if any(result.status is Status.ERROR and elem.path in selected for elem, result, _ in checked):
        print("Correct the errors above, or leave these projects out with --filter.")
        return env.ret_action_fail
    plans = [
        plan for elem, _, plan in checked if plan is not None and elem.path in selected and (plan.unreleased is False or "unreleased" in options)
    ]
    # any project that can deliver joins when a delivered project needs it (left out by the filter, or by the edition of the plan)
    optional = {plan.pom.key: plan for _, _, plan in checked if plan is not None and plan.pom is not None}
    if len(plans) == 0:
        print("Nothing to deliver.")
        return None
    # the dependencies between the Maven projects: the whole workspace, whatever the filter
    workspace, errors = deliver.read_workspace(mani.get_all_configs(use_filter=False), source, destination)
    for error in errors:
        print("Error: " + error)
    if len(errors) != 0:
        return env.ret_action_fail
    plans, chain = deliver.confirm_plans(
        plans, deliver.parse_bump(options.get("bump")), "yes" in options, lambda plans: deliver.chain_and_complete(plans, workspace, optional)
    )
    if len(plans) == 0:
        return env.ret_action_fail if len(chain.errors) != 0 else None
    if deliver.deliver_plans(plans, mani.deliver_mode):
        return env.ret_action_fail
    if deliver.follow_projects(workspace, chain):
        return env.ret_action_fail
    if "push" not in options:
        print("Push them with: island deliver-push")
        return None
    pushed = [plan.project for plan in plans] + [workspace[key].project for key in chain.follows]
    if deliver.push_projects(pushed, [destination, source]):
        return env.ret_action_fail
    return None
