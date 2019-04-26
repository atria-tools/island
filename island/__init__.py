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
import copy
# Local import
from . import host
from . import tools
from realog import debug
from . import env
from . import actions
import death.Arguments as arguments
import death.ArgElement as arg_element
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
	debug.verbose("island files: " + str(path) + " [START]")
	list_files = os.listdir(path)
	# filter elements:
	tmp_list_island_file = filter_name_and_file(path, list_files, env.get_system_base_name() + "*.py")
	debug.verbose("island files: " + str(path) + " : " + str(tmp_list_island_file))
	# Import the module:
	for filename in tmp_list_island_file:
		out.append(os.path.join(path, filename))
		debug.verbose("     Find a file : '" + str(out[-1]) + "'")
	return out


def init():
	global is_init;
	if is_init == True:
		return
	list_of_island_files = import_path_local(os.path.join(tools.get_current_path(__file__), 'actions'))
	
	actions.init(list_of_island_files)
	
	is_init = True

# initialize the system ...
init()


debug.verbose("List of actions: " + str(actions.get_list_of_action()))

my_args = arguments.Arguments()
my_args.add_section("option", "Can be set one time in all case")
my_args.add("h", "help", desc="Display this help")
my_args.add("v", "verbose", list=[["0","None"],["1","error"],["2","warning"],["3","info"],["4","debug"],["5","verbose"],["6","extreme_verbose"]], desc="display debug level (verbose) default =2")
my_args.add("c", "color", desc="Display message in color")
my_args.add("n", "no-fetch-manifest", haveParam=False, desc="Disable the fetch of the manifest")
my_args.set_stop_at(actions.get_list_of_action())
local_argument = my_args.parse()

##
## @brief Display the help of this makefile.
##
def usage():
	color = debug.get_color_set()
	# generic argument displayed : 
	my_args.display()
	print("		Action availlable" )
	list_actions = actions.get_list_of_action();
	for elem in list_actions:
		print("			" + color['green'] + elem + color['default'])
		print("					" + actions.get_action_help(elem))
	"""
	print("		" + color['green'] + "init" + color['default'])
	print("			initialize a 'island' interface with a manifest in a git ")
	print("		" + color['green'] + "sync" + color['default'])
	print("			Syncronise the currect environement")
	print("		" + color['green'] + "status" + color['default'])
	print("			Dump the status of the environement")
	"""
	print("	ex: " + sys.argv[0] + " -c init http://github.com/atria-soft/manifest.git")
	print("	ex: " + sys.argv[0] + " sync")
	exit(0)

def check_boolean(value):
	if    value == "" \
	   or value == "1" \
	   or value == "true" \
	   or value == "True" \
	   or value == True:
		return True
	return False

# preparse the argument to get the verbose element for debug mode
def parseGenericArg(argument, active):
	debug.extreme_verbose("parse arg : " + argument.get_option_name() + " " + argument.get_arg() + " active=" + str(active))
	if argument.get_option_name() == "help":
		if active == False:
			usage()
		return True
	elif argument.get_option_name()=="jobs":
		if active == True:
			#multiprocess.set_core_number(int(argument.get_arg()))
			pass
		return True
	elif argument.get_option_name()=="depth":
		if active == True:
			env.set_parse_depth(int(argument.get_arg()))
		return True
	elif argument.get_option_name() == "verbose":
		if active == True:
			debug.set_level(int(argument.get_arg()))
		return True
	elif argument.get_option_name() == "color":
		if active == True:
			if check_boolean(argument.get_arg()) == True:
				debug.enable_color()
			else:
				debug.disable_color()
		return True
	elif argument.get_option_name() == "no-fetch-manifest":
		if active == False:
			env.set_fetch_manifest(False)
		return True
	return False

"""
# open configuration of island:
config_file_name = "islandConfig.py"
config_file = os.path.join(tools.get_run_path(), config_file_name)
if os.path.isfile(config_file) == True:
	sys.path.append(os.path.dirname(config_file))
	debug.debug("Find basic configuration file: '" + config_file + "'")
	# the file exist, we can open it and get the initial configuration:
	configuration_file = __import__(config_file_name[:-3])
	
	if "get_exclude_path" in dir(configuration_file):
		data = configuration_file.get_exclude_path()
		debug.debug(" get default config 'get_exclude_path' val='" + str(data) + "'")
		env.set_exclude_search_path(data)
	
	if "get_parsing_depth" in dir(configuration_file):
		data = configuration_file.get_parsing_depth()
		debug.debug(" get default config 'get_parsing_depth' val='" + str(data) + "'")
		parseGenericArg(arg_element.ArgElement("depth", str(data)), True)
	
	if "get_default_jobs" in dir(configuration_file):
		data = configuration_file.get_default_jobs()
		debug.debug(" get default config 'get_default_jobs' val='" + str(data) + "'")
		parseGenericArg(arg_element.ArgElement("jobs", str(data)), True)
	
	if "get_default_color" in dir(configuration_file):
		data = configuration_file.get_default_color()
		debug.debug(" get default config 'get_default_color' val='" + str(data) + "'")
		parseGenericArg(arg_element.ArgElement("color", str(data)), True)
	
	if "get_default_debug_level" in dir(configuration_file):
		data = configuration_file.get_default_debug_level()
		debug.debug(" get default config 'get_default_debug_level' val='" + str(data) + "'")
		parseGenericArg(arg_element.ArgElement("verbose", str(data)), True)
	
	if "get_default_print_pretty" in dir(configuration_file):
		data = configuration_file.get_default_print_pretty()
		debug.debug(" get default config 'get_default_print_pretty' val='" + str(data) + "'")
		parseGenericArg(arg_element.ArgElement("pretty", str(data)), True)
	
	if "get_default_force_optimisation" in dir(configuration_file):
		data = configuration_file.get_default_force_optimisation()
		debug.debug(" get default config 'get_default_force_optimisation' val='" + str(data) + "'")
		parseGenericArg(arg_element.ArgElement("force-optimisation", str(data)), True)
	
	if "get_default_isolate_system" in dir(configuration_file):
		data = configuration_file.get_default_isolate_system()
		debug.debug(" get default config 'get_default_isolate_system' val='" + str(data) + "'")
		parseGenericArg(arg_element.ArgElement("isolate-system", str(data)), True)
		
"""

# parse default unique argument:
for argument in local_argument:
	parseGenericArg(argument, True)

# remove all generic arguments:
new_argument_list = []
for argument in local_argument:
	if parseGenericArg(argument, False) == True:
		continue
	new_argument_list.append(argument)

# now the first argument is: the action:
if len(new_argument_list) == 0:
	debug.warning("--------------------------------------")
	debug.warning("Missing the action to do ...")
	debug.warning("--------------------------------------")
	usage()


# TODO : move tin in actions ...
list_actions = actions.get_list_of_action();

action_to_do = new_argument_list[0].get_arg()
new_argument_list = new_argument_list[1:]
if action_to_do not in list_actions:
	debug.warning("--------------------------------------")
	debug.warning("Wrong action type : '" + str(action_to_do) + "' availlable list: " + str(list_actions) )
	debug.warning("--------------------------------------")
	usage()

# todo : Remove this
if     action_to_do != "init" \
   and os.path.exists(env.get_island_path()) == False:
	debug.error("Can not execute a island cmd if we have not initialize a config: '" + str("." + env.get_system_base_name()) + "' in upper 6 parent path")
	exit(-1)


actions.execute(action_to_do, my_args.get_last_parsed()+1)

# stop all started threads;
#multiprocess.un_init()


