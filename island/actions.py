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
## @param[in] function_name (string) Name of the fucntion to call
## @param[in] default_value (*) Renurned value of the call if function does not exist
## @return (*) the getted value or the default_value
##
def get_function_value(action_name, function_name, default_value = None):
	global list_actions;
	for elem in list_actions:
		if elem["name"] == action_name:
			# finish the parsing
			sys.path.append(os.path.dirname(elem["path"]))
			the_action = __import__(__base_action_name + action_name)
			if function_name not in dir(the_action):
				return default_value
			method_to_call = getattr(the_action, function_name)
			return method_to_call()
	return default_value

##
## @brief Get the global help value of a module
## @param[in] action_name (string) Name of the action
## @return The first line of description
##
def get_action_help(action_name):
	value = get_function_value(action_name, "help", "---")
	return value.split("\n")[0]


def usage(arguments, action_name):
	color = debug.get_color_set()
	# generic argument displayed for specific action:
	#print("Specific argument for the command: '" + action_name + "'" )
	#print("    " + get_desc(action_name))
	value = get_function_value(action_name, "help")
	debug.info("Description:")
	debug.info("\t" + str(value))
	arguments.display(action_name)
	value = get_function_value(action_name, "help_example")
	if value != None:
		debug.info("Example:")
		for elem in value.split("\n"):
			debug.info("\t" + value)
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
		have_unknow_argument = False
		if "have_unknow_argument" in dir(the_action):
			have_unknow_argument = the_action.have_unknow_argument()
		my_under_args = my_under_args_parser.parse(argument_start_id, have_unknow_argument)
		# search help if needed ==> permit to not duplicating code
		for elem in my_under_args:
			if elem.get_option_name() == "help":
				usage(my_under_args_parser, action_name)
				return 0
		# now we can execute:
		if "execute" not in dir(the_action):
			debug.error("execute is not implmented for this action ... '" + str(action_name) + "'")
			return -11
		debug.info("execute: " + action_name)
		for elem in my_under_args:
			debug.debug("    " + str(elem.get_option_name()) + "='" + str(elem.get_arg()) + "'")
		ret = the_action.execute(my_under_args)
		if ret == None:
			return 0
		debug.info("    ==========================")
		debug.info("    ==  Some error occured  ==")
		debug.info("    ==========================")
		return ret
	debug.error("Can not do the action...")
	return -10
