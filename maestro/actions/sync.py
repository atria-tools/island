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
from lxml import etree


def help():
	return "plop"

def load_manifest(file):
	tree = etree.parse(file)
	debug.info("manifest:")
	root = tree.getroot()
	if root.tag != "manifest":
		debug.error("in '" + str(file) + "' have not main xml node='manifest'")
	for child in root:
		if type(child) == etree._Comment:
			debug.info("    comment='" + str(child.text) + "'");
		else:
			debug.info("    '" + str(child.tag) + "' values=" + str(child.attrib));
	# inside data    child.text
	return "";


def execute(arguments):
	debug.info("execute:")
	for elem in arguments:
		debug.info("    '" + str(elem.get_arg()) + "'")
	if len(arguments) != 0:
		debug.error("Sync have not parameter")
	
	# check if .XXX exist (create it if needed)
	base_path = os.path.join(tools.get_run_path(), "." + env.get_system_base_name())
	base_config = os.path.join(base_path, "config.txt")
	base_manifest_repo = os.path.join(base_path, "manifest")
	if    os.path.exists(base_path) == False \
	   or os.path.exists(base_config) == False \
	   or os.path.exists(base_manifest_repo) == False:
		debug.error("System already init have an error: missing data: '" + str(base_path) + "'")
	
	config_property = tools.file_read_data(base_config)
	
	element_config = config_property.split("\n")
	if len(element_config) != 3:
		debug.error("error in configuration property")
	if element_config[0][:5] != "repo=":
		debug.error("error in configuration property (2)")
	if element_config[1][:7] != "branch=":
		debug.error("error in configuration property (3)")
	if element_config[2][:5] != "file=":
		debug.error("error in configuration property (4)")
	configuration = {
	    "repo":element_config[0][5:],
	    "branch":element_config[1][7:],
	    "file":element_config[2][5:]
	    }
	debug.info("configuration property: " + str(configuration))
	
	file_source_manifest = os.path.join(base_manifest_repo, configuration["file"])
	if os.path.exists(file_source_manifest) == False:
		debug.error("Missing manifest file : '" + str(file_source_manifest) + "'")
	
	manifest = load_manifest(file_source_manifest)
	