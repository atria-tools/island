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
from . import debug
import os
import sys
from . import env

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
				debug.error("execute is not implmented for this action ... '" + str(action_name) + "'")
				return None
			return the_action.get_desc()
	return None


def execute(action_name, argument_list):
	global list_actions;
	# TODO: Move here the check if action is availlable
	
	for elem in list_actions:
		if elem["name"] == action_name:
			debug.info("action: " + str(elem));
			# finish the parsing
			sys.path.append(os.path.dirname(elem["path"]))
			the_action = __import__(__base_action_name + action_name)
			if "execute" not in dir(the_action):
				debug.error("execute is not implmented for this action ... '" + str(action_name) + "'")
				return False
			return the_action.execute(argument_list)
	debug.error("Can not do the action...")
	return False
