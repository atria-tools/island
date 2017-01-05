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

list_actions = []

def init(files):
	global list_actions;
	debug.debug("List of action for maestro: ")
	for elem_path in files :
		debug.debug("    '" + os.path.basename(elem_path)[:-3] + "' file=" + elem_path)
		list_actions.append({
		    "name":os.path.basename(elem_path)[:-3],
		    "path":elem_path,
		    })
	

def get_list_of_action():
	global list_actions;
	out = []
	for elem in list_actions:
		out.append(elem["name"])
	return out



def execute(action_to_do, argument_list):
	global list_actions;
	# TODO: Move here the check if action is availlable
	
	for elem in list_actions:
		if elem["name"] == action_to_do:
			debug.info("action: " + str(elem));
			# finish the parsing
			sys.path.append(os.path.dirname(elem["path"]))
			the_action = __import__(action_to_do)
			if "execute" not in dir(the_action):
				debug.error("execute is not implmented for this action ... '" + str(action_to_do) + "'")
				return False
			return the_action.execute(argument_list)
	debug.error("Can not do the action...")
	return False
