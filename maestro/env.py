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



force_mode=False

def set_force_mode(val):
	global force_mode
	if val==1:
		force_mode = 1
	else:
		force_mode = 0

def get_force_mode():
	global force_mode
	return force_mode

force_optimisation=False

def set_force_optimisation(val):
	global force_optimisation
	if val==1:
		force_optimisation = 1
	else:
		force_optimisation = 0

def get_force_optimisation():
	global force_optimisation
	return force_optimisation

isolate_system=False

def set_isolate_system(val):
	global isolate_system
	if val==1:
		isolate_system = 1
	else:
		isolate_system = 0

def get_isolate_system():
	global isolate_system
	return isolate_system

parse_depth = 9999999

def set_parse_depth(val):
	global parse_depth
	parse_depth = val
	debug.debug("Set depth search element: " + str(parse_depth))

def get_parse_depth():
	global parse_depth
	return parse_depth

exclude_search_path = []

def set_exclude_search_path(val):
	global exclude_search_path
	exclude_search_path = val
	debug.debug("Set depth search element: " + str(exclude_search_path))

def get_exclude_search_path():
	global exclude_search_path
	return exclude_search_path


system_base_name = "maestro"

def set_system_base_name(val):
	global system_base_name
	system_base_name = val
	debug.debug("Set basename: '" + str(system_base_name) + "'")

def get_system_base_name():
	global system_base_name
	return system_base_name

