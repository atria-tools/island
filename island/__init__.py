#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Inland main().

@author Edouard DUPIN
@copyright 2012, Edouard DUPIN, all right reserved
@license MPL v2.0 (see license file)
"""

import copy
import fnmatch
import os
import sys
from typing import Union

import death.ArgElement as arg_element
import death.Arguments as arguments
from realog import debug

# Local import
from . import (
    actions,
    env,
    host,
    tools,
)


is_init = False

debug.set_display_on_error("    ==========================\n    ==  Some error occurred  ==\n    ==========================")


def init() -> None:
    """Global initialization of Island."""
    global is_init
    if is_init is True:
        return
    # import local island files
    list_of_island_files = tools.import_path_local(
        os.path.join(tools.get_current_path(__file__), "actions"),
        base_name=env.get_system_base_name() + "*.py",
    )
    actions.init(list_of_island_files)
    # import project actions files
    list_of_island_files = tools.import_path_local(
        env.get_island_root_path(),
        2,
        [".island", ".git", "archive"],
        base_name=env.get_system_base_name() + "*.py",
    )
    actions.init(list_of_island_files)
    is_init = True


# initialize the system ...
init()

debug.verbose("List of actions: " + str(actions.get_list_of_action()))

my_args = arguments.Arguments()
my_args.add_section("option", "Can be set one time in all case")
my_args.add("h", "help", desc="Display this help")
my_args.add(
    "v",
    "verbose",
    list=[
        ["0", "None"],
        ["1", "error"],
        ["2", "warning"],
        ["3", "info"],
        ["4", "debug"],
        ["5", "verbose"],
        ["6", "extreme_verbose"],
    ],
    desc="display debug level (verbose) default =2",
)
my_args.add("c", "color", desc="Display message in color")
my_args.add("n", "no-fetch-manifest", haveParam=False, desc="Disable the fetch of the manifest")
my_args.add(
    "F",
    "filter",
    haveParam=True,
    desc="Filter the action on a list of path or subpath: -f library",
)
my_args.add(
    "f",
    "folder",
    haveParam=False,
    desc="Display the folder instead of the git repository name",
)
my_args.add(
    "w",
    "wait",
    haveParam=True,
    desc="Wait between 2 access on the server (needed when the server is really slow to remove ssh connection) (default="
    + str(env.get_wait_between_sever_command())
    + ")",
)
my_args.set_stop_at(actions.get_list_of_action())
local_argument = my_args.parse()


def usage() -> None:
    """Display the help of Island."""
    color = debug.get_color_set()
    # Generic argument displayed :
    my_args.display()
    print("		Action available")
    list_actions = actions.get_list_of_action()
    for elem in list_actions:
        print(f"			{color['green']}{elem}{color['default']}")
        print(f"					{actions.get_action_help(elem)}")
    """
    print("		{color['green']}init{color['default']}")
    print("			initialize a 'island' interface with a manifest in a git ")
    print("		{color['green']}sync{color['default']}")
    print("			Synchronize the current environnement")
    print("		{color['green']}status{color['default']}")
    print("			Dump the status of the environnement")
    """
    print(f"	ex: {sys.argv[0]} -c init http://github.com/atria-soft/manifest.git")
    print(f"	ex: {sys.argv[0]} sync")
    exit(0)


def check_boolean(value: Union[bool, str]) -> bool:
    """Check if the value is a real boolean or a boolean string and return the boolean value.

    :param value: Value to check.
    :return: Equivalent boolean value.
    """
    if value == "" or value == "1" or value == "true" or value == "True" or value is True:
        return True
    return False


def parse_generic_arg(argument: arg_element.ArgElement, active: bool) -> bool:
    """Keep global args that have no dependence with the mode.

    :param argument: _description_
    :param active: _description_
    :return: _description_
    """
    debug.extreme_verbose(f"parse arg : {argument.get_option_name()} {argument.get_arg()} active={active}")
    if argument.get_option_name() == "help":
        if active is False:
            usage()
        return True
    elif argument.get_option_name() == "jobs":
        if active is True:
            # multiprocess.set_core_number(int(argument.get_arg()))
            pass
        return True
    elif argument.get_option_name() == "wait":
        if active is True:
            env.set_wait_between_sever_command(int(argument.get_arg()))
        return True
    elif argument.get_option_name() == "verbose":
        if active is True:
            debug.set_level(int(argument.get_arg()))
        return True
    elif argument.get_option_name() == "folder":
        if active is True:
            env.set_display_folder_instead_of_git_name(True)
        return True
    elif argument.get_option_name() == "color":
        if active is True:
            if check_boolean(argument.get_arg()) is True:
                debug.enable_color()
            else:
                debug.disable_color()
        return True
    elif argument.get_option_name() == "filter":
        if active is True:
            env.set_filter_command(str(argument.get_arg()))
        return True
    elif argument.get_option_name() == "no-fetch-manifest":
        if active is False:
            env.set_fetch_manifest(False)
        return True
    return False


# open configuration of island:
config_file = env.get_island_path_user_config()
if os.path.isfile(config_file) is True:
    sys.path.append(os.path.dirname(config_file))
    debug.debug(f"Find basic configuration file: '{config_file}'")
    # the file exist, we can open it and get the initial configuration:
    configuration_file = __import__(env.get_system_config_name()[:-3])

    if "get_exclude_path" in dir(configuration_file):
        data = configuration_file.get_exclude_path()
        debug.debug(f"get default config 'get_exclude_path' val='{data}'")
        env.set_exclude_search_path(data)

    if "get_default_color" in dir(configuration_file):
        data = configuration_file.get_default_color()
        debug.debug(f"get default config 'get_default_color' val='{data}'")
        parse_generic_arg(arg_element.ArgElement("color", str(data)), True)

    if "get_default_debug_level" in dir(configuration_file):
        data = configuration_file.get_default_debug_level()
        debug.debug(f"get default config 'get_default_debug_level' val='{data}'")
        parse_generic_arg(arg_element.ArgElement("verbose", str(data)), True)

    if "get_default_folder" in dir(configuration_file):
        data = configuration_file.get_default_folder()
        debug.debug(f"get default config 'get_default_folder' val='{data}'")
        parse_generic_arg(arg_element.ArgElement("folder", str(data)), True)

    if "get_default_wait" in dir(configuration_file):
        data = configuration_file.get_default_wait()
        debug.debug(f"get default config 'get_default_wait' val='{data}'")
        parse_generic_arg(arg_element.ArgElement("wait", str(data)), True)

    if "get_default_filter" in dir(configuration_file):
        data = configuration_file.get_default_filter()
        debug.debug(f"get default config 'get_default_filter' val='{data}'")
        parse_generic_arg(arg_element.ArgElement("filter", str(data)), True)


# parse default unique argument:
for argument in local_argument:
    parse_generic_arg(argument, True)

# remove all generic arguments:
new_argument_list = []
for argument in local_argument:
    if parse_generic_arg(argument, False) is True:
        continue
    new_argument_list.append(argument)

# now the first argument is: the action:
if len(new_argument_list) == 0:
    debug.warning("--------------------------------------")
    debug.warning("Missing the action to do ...")
    debug.warning("--------------------------------------")
    usage()


# TODO : move tin in actions ...
list_actions = actions.get_list_of_action()

action_to_do = new_argument_list[0].get_arg()
new_argument_list = new_argument_list[1:]
if action_to_do not in list_actions:
    debug.warning("--------------------------------------")
    debug.warning(f"Wrong action type : '{action_to_do}' available list: {list_actions}")
    debug.warning("--------------------------------------")
    usage()

# todo : Remove this
if action_to_do != "init" and os.path.exists(env.get_island_path()) is False:
    debug.error(f"Can not execute a island cmd if we have not initialize a config: '.{env.get_system_base_name()}' in upper 6 parent path")
    exit(-1)


ret = actions.execute(action_to_do, my_args.get_last_parsed() + 1)

exit(ret)
# stop all started threads;
# multiprocess.un_init()
