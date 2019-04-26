#!/usr/bin/python
# -*- coding: utf-8 -*-
##
## @author Edouard DUPIN
##
## @copyright 2012, Edouard DUPIN, all right reserved
##
## @license MPL v2.0 (see license file)
##

# Local import
from realog import debug
import os
import sys
from . import env
import death.Arguments as arguments

list_actions = []

__base_action_name = env.get_system_base_name() + "Action_"

def init(files):
	global list_actions;
	debug.debug("List of action for island: ")
	for elem_path in files :
		base_name = os.path.basename(elem_path)
		if len(base_name) <= 3 + len(__base_action_name):
			# reject it, too small
			continue
		base_name = base_name[:-3]
		if base_name[:len(__base_action_name)] != __base_action_name:
			# reject it, wrong start file
			continue
		name_action = base_name[len(__base_action_name):]
		debug.debug("    '" + os.path.basename(elem_path)[:-3] + "' file=" + elem_path)
		list_actions.append({
		    "name":name_action,
		    "path":elem_path,
		    })

##
## @brief Get the wall list of action availlable
## @return ([string]) the list of action name
##
def get_list_of_action():
	global list_actions;
	out = []
	for elem in list_actions:
		out.append(elem["name"])
	return out

##
## @brief Get a description of an action
## @param[in] action_name (string) Name of the action
## @return (string/None) A descriptive string or None
##
def get_desc(action_name):
	global list_actions;
	for elem in list_actions:
		if elem["name"] == action_name:
			# finish the parsing
			sys.path.append(os.path.dirname(elem["path"]))
			the_action = __import__(__base_action_name + action_name)
			if "get_desc" not in dir(the_action):
				return ""
			return the_action.get_desc()
	return ""


def usage(arguments, action_name):
	color = debug.get_color_set()
	# generic argument displayed for specific action:
	print("Specific argument for the command: '" + action_name + "'" )
	print("    " + get_desc(action_name))
	arguments.display(action_name)
	exit(0)

def execute(action_name, argument_start_id):
	global list_actions;
	# TODO: Move here the check if action is availlable
	
	for elem in list_actions:
		if elem["name"] != action_name:
			continue
		debug.info("action: " + str(elem));
		# finish the parsing
		sys.path.append(os.path.dirname(elem["path"]))
		the_action = __import__(__base_action_name + action_name)
		my_under_args_parser = arguments.Arguments()
		my_under_args_parser.add("h", "help", desc="Help of this action")
		if "add_specific_arguments" in dir(the_action):
			the_action.add_specific_arguments(my_under_args_parser, elem["name"])
		my_under_args = my_under_args_parser.parse(argument_start_id)
		# search help if needed ==> permit to not duplicating code
		for elem in my_under_args:
			if elem.get_option_name() == "help":
				usage(my_under_args_parser, action_name)
				return False
		# now we can execute:
		if "execute" not in dir(the_action):
			debug.error("execute is not implmented for this action ... '" + str(action_name) + "'")
			return False
		debug.info("execute: " + action_name)
		for elem in my_under_args:
			debug.info("    " + str(elem.get_option_name()) + "='" + str(elem.get_arg()) + "'")
		return the_action.execute(my_under_args)
	debug.error("Can not do the action...")
	return False

def get_action_help(action_name):
	global list_actions;
	for elem in list_actions:
		if elem["name"] != action_name:
			continue
		sys.path.append(os.path.dirname(elem["path"]))
		the_action = __import__(__base_action_name + action_name)
		if "help" in dir(the_action):
			return the_action.help()
	return "---"
