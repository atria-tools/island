#!/usr/bin/python
# -*- coding: utf-8 -*-
##
## @author Edouard DUPIN
##
## @copyright 2012, Edouard DUPIN, all right reserved
##
## @license MPL v2.0 (see license file)
##

from maestro import debug
from maestro import tools
from maestro import env
from maestro import multiprocess
import os

def help():
	return "plop"

def execute(arguments):
	debug.info("execute:")
	for elem in arguments:
		debug.info("    '" + str(elem.get_arg()) + "'")
	if len(arguments) == 0:
		debug.error("Missing argument to execute the current action ...")
	
	# the configuration availlable:
	branch = "master"
	manifest_name = "default.xml"
	address_manifest = ""
	for elem in arguments:
		if elem.get_option_name() == "branch":
			debug.info("find branch name: '" + elem.get_arg() + "'")
			branch = elem.get_arg()
		elif elem.get_option_name() == "manifest":
			debug.info("find mmanifest name: '" + elem.get_arg() + "'")
			manifest_name = elem.get_arg()
		elif elem.get_option_name() == "":
			if address_manifest != "":
				debug.error("Manifest adress already set : '" + address_manifest + "' !!! '" + elem.get_arg() + "'")
			address_manifest = elem.get_arg()
		else:
			debug.error("Wrong argument: '" + elem.get_option_name() + "' '" + elem.get_arg() + "'")
	
	if address_manifest == "":
		debug.error("Init: Missing manifest name")
	
	debug.info("Init with: '" + address_manifest + "' branch='" + branch + "' name of manifest='" + manifest_name + "'")
	
	
	# check if .XXX exist (create it if needed)
	base_path = os.path.join(tools.get_run_path(), "." + env.get_system_base_name())
	base_config = os.path.join(base_path, "config.txt")
	base_manifest_repo = os.path.join(base_path, "manifest")
	if     os.path.exists(base_path) == True \
	   and os.path.exists(base_config) == True \
	   and os.path.exists(base_manifest_repo) == True:
		debug.error("System already init: path already exist: '" + str(base_path) + "'")
	tools.create_directory(base_path)
	# check if the git of the manifest if availlable
	
	# create the file configuration:
	data = "repo=" + address_manifest + "\nbranch=" + branch + "\nfile=" + manifest_name
	tools.file_write_data(base_config, data)
	
	#clone the manifest repository
	cmd = "git clone " + address_manifest + " --branch " + branch + " " + base_manifest_repo
	
	debug.info("clone the manifest")
	ret = multiprocess.run_command_direct(cmd)
	
	if ret == "":
		return True
	
	if ret == False:
		# all is good, ready to get the system work corectly
		return True
	debug.info("'" + ret + "'")
	debug.error("Init does not work")
	return False


