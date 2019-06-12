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


system_base_name = "island"

def set_system_base_name(val):
	global system_base_name
	system_base_name = val
	debug.debug("Set basename: '" + str(system_base_name) + "'")

def get_system_base_name():
	global system_base_name
	return system_base_name


fetch_manifest = True

def set_fetch_manifest(val):
	global fetch_manifest
	fetch_manifest = val

def get_fetch_manifest():
	global fetch_manifest
	return fetch_manifest


wait_between_sever_command = 0

def set_wait_between_sever_command(val):
	global wait_between_sever_command
	wait_between_sever_command = val

def get_wait_between_sever_command():
	global wait_between_sever_command
	return wait_between_sever_command

display_folder_instead_of_git_name = True

def set_display_folder_instead_of_git_name(val):
	global display_folder_instead_of_git_name
	display_folder_instead_of_git_name = val

def get_display_folder_instead_of_git_name():
	global display_folder_instead_of_git_name
	return display_folder_instead_of_git_name

island_root_path = os.path.join(os.getcwd())
if os.path.exists(os.path.join(island_root_path, "." + get_system_base_name())) == True:
	# all is good ...
	pass
elif os.path.exists(os.path.join(island_root_path, "..", "." + get_system_base_name())) == True:
	island_root_path = os.path.join(os.getcwd(), "..")
elif os.path.exists(os.path.join(island_root_path, "..", "..", "." + get_system_base_name())) == True:
	island_root_path = os.path.join(os.getcwd(), "..", "..")
elif os.path.exists(os.path.join(island_root_path, "..", "..", "..", "." + get_system_base_name())) == True:
	island_root_path = os.path.join(os.getcwd(), "..", "..", "..")
elif os.path.exists(os.path.join(island_root_path, "..", "..", "..", "..", "." + get_system_base_name())) == True:
	island_root_path = os.path.join(os.getcwd(), "..", "..", "..", "..")
elif os.path.exists(os.path.join(island_root_path, "..", "..", "..", "..", "..", "." + get_system_base_name())) == True:
	island_root_path = os.path.join(os.getcwd(), "..", "..", "..", "..", "..")
elif os.path.exists(os.path.join(island_root_path, "..", "..", "..", "..", "..", "..", "." + get_system_base_name())) == True:
	island_root_path = os.path.join(os.getcwd(), "..", "..", "..", "..", "..", "..")
else:
	#debug.error("the root path of " + get_system_base_name() + " must not be upper that 6 parent path")
	pass
island_path = os.path.join(island_root_path, "." + get_system_base_name())
island_path_config = os.path.join(island_path, "config.txt")
island_path_manifest = os.path.join(island_path, "manifest")

##
## @brief to use later to know where the ".island" parent path is ...
## @return the parent path of the ".island"
##
def get_island_root_path():
	global island_root_path
	return island_root_path

def get_island_path():
	global island_path
	return island_path

def get_island_path_config():
	global island_path_config
	return island_path_config

def get_island_path_manifest():
	global island_path_manifest
	return island_path_manifest


