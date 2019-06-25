#!/usr/bin/python
# -*- coding: utf-8 -*-
##
## @author Edouard DUPIN
##
## @copyright 2012, Edouard DUPIN, all right reserved
##
## @license MPL v2.0 (see license file)
##

from realog import debug
from island import tools
from island import env
from island import config
from island import multiprocess
from island import manifest
from island import commands
import os


def help():
	return "Syncronize all the repository referenced"


def add_specific_arguments(my_args, section):
	pass

def execute(arguments):
	for elem in arguments:
		debug.error("pull Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")
	
	# check if .XXX exist (create it if needed)
	if    os.path.exists(env.get_island_path()) == False \
	   or os.path.exists(env.get_island_path_config()) == False \
	   or os.path.exists(env.get_island_path_manifest()) == False:
		debug.error("System already init have an error: missing data: '" + str(env.get_island_path()) + "'")
	
	configuration = config.Config()
	
	debug.info("update manifest : '" + str(env.get_island_path_manifest()) + "'")
	is_modify_manifest = commands.check_repository_is_modify(env.get_island_path_manifest())
	if is_modify_manifest == True:
		commands.fetch(env.get_island_path_manifest(), "origin")
	else:
		commands.pull(env.get_island_path_manifest(), "origin")
	