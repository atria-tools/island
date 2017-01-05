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
is_init = False

"""
def filter_name_and_file(root, list_files, filter):
	# filter elements:
	tmp_list = fnmatch.filter(list_files, filter)
	out = []
	for elem in tmp_list:
		if os.path.isfile(os.path.join(root, elem)) == True:
			out.append(elem);
	return out;

def filter_path(root, list_files):
	out = []
	for elem in list_files:
		if    len(elem) == 0 \
		   or elem[0] == '.':
			continue
		if os.path.isdir(os.path.join(root, elem)) == True:
			out.append(elem);
	return out;

def import_path_local(path, limit_sub_folder, exclude_path = [], base_name = ""):
	out = []
	debug.verbose("maestro files: " + str(path) + " [START]")
	if limit_sub_folder == 0:
		debug.debug("Subparsing limitation append ...")
		return []
	try:
		list_files = os.listdir(path)
	except:
		# an error occure, maybe read error ...
		debug.warning("error when getting subdirectory of '" + str(path) + "'")
		return []
	if path in exclude_path:
		debug.debug("find '" + str(path) + "' in exclude_path=" + str(exclude_path))
		return []
	# filter elements:
	tmp_list_maestro_file = filter_name_and_file(path, list_files, base_name + "*.py")
	debug.verbose("maestro files: " + str(path) + " : " + str(tmp_list_maestro_file))
	# Import the module:
	for filename in tmp_list_maestro_file:
		out.append(os.path.join(path, filename))
		debug.extreme_verbose("     Find a file : '" + str(out[-1]) + "'")
	need_parse_sub_folder = True
	rm_value = -1
	# check if we need to parse sub_folder
	if len(tmp_list_maestro_file) != 0:
		need_parse_sub_folder = False
	# check if the file "maestro_parse_sub.py" is present ==> parse SubFolder (force and add +1 in the resursing
	if base_name + "ParseSubFolders.txt" in list_files:
		debug.debug("find SubParser ... " + str(base_name + "ParseSubFolders.txt") + " " + path)
		data_file_sub = tools.file_read_data(os.path.join(path, base_name + "ParseSubFolders.txt"))
		if data_file_sub == "":
			debug.debug("    Empty file Load all subfolder in the worktree in '" + str(path) + "'")
			need_parse_sub_folder = True
			rm_value = 0
		else:
			list_sub = data_file_sub.split("\n")
			debug.debug("    Parse selected folders " + str(list_sub) + " no parse local folder directory")
			need_parse_sub_folder = False
			for folder in list_sub:
				if    folder == "" \
				   or folder == "/":
					continue;
				tmp_out = import_path_local(os.path.join(path, folder),
				                            1,
				                            exclude_path,
				                            base_name)
				# add all the elements:
				for elem in tmp_out:
					out.append(elem)
	if need_parse_sub_folder == True:
		list_folders = filter_path(path, list_files)
		for folder in list_folders:
			tmp_out = import_path_local(os.path.join(path, folder),
			                            limit_sub_folder - rm_value,
			                            exclude_path,
			                            base_name)
			# add all the elements:
			for elem in tmp_out:
				out.append(elem)
	return out
"""

def init():
	global is_init;
	if is_init == True:
		return
	"""
	debug.verbose("Use Make as a make stadard")
	sys.path.append(tools.get_run_path())
	# create the list of basic folder:
	basic_folder_list = []
	basic_folder_list.append([tools.get_current_path(__file__), True])
	# Import all sub path without out and archive
	for elem_path in os.listdir("."):
		if os.path.isdir(elem_path) == False:
			continue
		if    elem_path.lower() == "android" \
		   or elem_path == "out" :
			continue
		debug.debug("Automatic load path: '" + elem_path + "'")
		basic_folder_list.append([elem_path, False])
	
	# create in a single path the basic list of maestro files  (all start with maestro and end with .py)
	exclude_path = env.get_exclude_search_path()
	limit_sub_folder = env.get_parse_depth()
	list_of_maestro_files = []
	for elem_path, is_system in basic_folder_list:
		if is_system == True:
			limit_sub_folder_tmp = 999999
		else:
			limit_sub_folder_tmp = limit_sub_folder
		tmp_out = import_path_local(elem_path,
		                            limit_sub_folder_tmp,
		                            exclude_path,
		                            env.get_build_system_base_name())
		# add all the elements:
		for elem in tmp_out:
			list_of_maestro_files.append(elem)
	
	debug.debug("Files specific maestro: ")
	for elem_path in list_of_maestro_files:
		debug.debug("    " + elem_path)
	# simply import element from the basic list of files (single parse ...)
	builder.import_path(list_of_maestro_files)
	module.import_path(list_of_maestro_files)
	system.import_path(list_of_maestro_files)
	target.import_path(list_of_maestro_files)
	macro.import_path(list_of_maestro_files)
	
	builder.init()
	"""
	is_init = True


