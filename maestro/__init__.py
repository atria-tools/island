#!/usr/bin/python
# -*- coding: utf-8 -*-
##
## @author Edouard DUPIN
##
## @copyright 2012, Edouard DUPIN, all right reserved
##
## @license MPL v2.0 (see license file)
##
import os
import sys
import fnmatch
# Local import
from . import host
from . import tools
from . import debug
from . import env
from . import actions
is_init = False


def filter_name_and_file(root, list_files, filter):
	# filter elements:
	tmp_list = fnmatch.filter(list_files, filter)
	out = []
	for elem in tmp_list:
		if os.path.isfile(os.path.join(root, elem)) == True:
			out.append(elem);
	return out;

def import_path_local(path):
	out = []
	debug.verbose("maestro files: " + str(path) + " [START]")
	list_files = os.listdir(path)
	# filter elements:
	tmp_list_maestro_file = filter_name_and_file(path, list_files, "*.py")
	debug.verbose("maestro files: " + str(path) + " : " + str(tmp_list_maestro_file))
	# Import the module:
	for filename in tmp_list_maestro_file:
		out.append(os.path.join(path, filename))
		debug.verbose("     Find a file : '" + str(out[-1]) + "'")
	return out


def init():
	global is_init;
	if is_init == True:
		return
	list_of_maestro_files = import_path_local(os.path.join(tools.get_current_path(__file__), 'actions'))
	
	actions.init(list_of_maestro_files)
	
	is_init = True


