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


system_base_name = "maestro"

def set_system_base_name(val):
	global system_base_name
	system_base_name = val
	debug.debug("Set basename: '" + str(system_base_name) + "'")

def get_system_base_name():
	global system_base_name
	return system_base_name



maestro_root_path = os.path.join(os.getcwd())
maestro_path = os.path.join(maestro_root_path, "." + get_system_base_name())
maestro_path_config = os.path.join(maestro_path, "config.txt")
maestro_path_manifest = os.path.join(maestro_path, "manifest")

##
## @brief to use later to know where the ".maestro" parent path is ...
## @return the parent path of the ".maestro"
##
def get_maestro_root_path():
	global maestro_root_path
	return maestro_root_path

def get_maestro_path():
	global maestro_path
	return maestro_path

def get_maestro_path_config():
	global maestro_path_config
	return maestro_path_config

def get_maestro_path_manifest():
	global maestro_path_manifest
	return maestro_path_manifest


