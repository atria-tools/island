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


system_base_name = "island"

def set_system_base_name(val):
	global system_base_name
	system_base_name = val
	debug.debug("Set basename: '" + str(system_base_name) + "'")

def get_system_base_name():
	global system_base_name
	return system_base_name



island_root_path = os.path.join(os.getcwd())
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


