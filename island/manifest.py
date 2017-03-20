#!/usr/bin/python
# -*- coding: utf-8 -*-
##
## @author Edouard DUPIN
##
## @copyright 2012, Edouard DUPIN, all right reserved
##
## @license MPL v2.0 (see license file)
##
import platform
import sys
import os
import copy
# Local import
from . import debug
from . import tools
from . import env

from lxml import etree


def load_config():
	config_property = tools.file_read_data(env.get_island_path_config())
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
	return configuration


class RepoConfig():
	def __init__(self):
		self.name = ""
		self.path = ""
		self.remotes = [] # list of all remotes, with the upstream elements (needed for third party integrations)
		self.select_remote = ""
		self.branch = ""
		

class Manifest():
	def __init__(self, manifest_xml):
		self.manifest_xml = manifest_xml
		self.projects = []
		self.default = None
		self.default_base = {
		    "remote":"origin",
		    "revision":"master",
		    "sync":False,
		    }
		self.remotes = []
		self.includes = []
		# load the manifest
		self._load()
		# check error in manifest (double path ...)
		self._check_double_path([])
	
	def _load(self):
		tree = etree.parse(self.manifest_xml)
		debug.debug("manifest : '" + self.manifest_xml + "'")
		root = tree.getroot()
		if root.tag != "manifest":
			debug.error("(l:" + str(child.sourceline) + ") in '" + str(file) + "' have not main xml node='manifest'")
		for child in root:
			if type(child) == etree._Comment:
				debug.verbose("(l:" + str(child.sourceline) + ")     comment='" + str(child.text) + "'");
				continue
			if child.tag == "remote":
				name = "origin"
				fetch = ""
				for attr in child.attrib:
					if attr == "name":
						name = child.attrib[attr]
					elif attr == "fetch":
						fetch = child.attrib[attr]
						while     len(fetch) > 1 \
						      and (    fetch[-1] == "\\" \
						            or fetch[-1] == "/") :
							fetch = fetch[:-1]
					else:
						debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest : Unknow '" + child.tag + "'  attibute : '" + attr + "', availlable:[name,fetch]")
				debug.debug("(l:" + str(child.sourceline) + ")     find '" + child.tag + "' : name='" + name + "' fetch='" + fetch + "'");
				self.remotes.append({
				    "name":name,
				    "fetch":fetch
				    })
				continue
			if child.tag == "include":
				name = ""
				for attr in child.attrib:
					if attr == "name":
						name = child.attrib[attr]
					else:
						debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest : Unknow '" + child.tag + "'  attibute : '" + attr + "', availlable:[name]")
				debug.debug("(l:" + str(child.sourceline) + ")     find '" + child.tag + "' : name='" + name + "'");
				# check if the file exist ...
				new_name_xml = os.path.join(os.path.dirname(self.manifest_xml),name)
				if os.path.exists(new_name_xml) == False:
					debug.error("(l:" + str(child.sourceline) + ") The file does not exist : '" + new_name_xml + "'")
				self.includes.append({
				    "name":name,
				    "path":new_name_xml,
				    "manifest":None
				    })
				continue
			if child.tag == "default":
				remote = "origin"
				revision = "master"
				sync = False
				for attr in child.attrib:
					if attr == "remote":
						remote = child.attrib[attr]
					elif attr == "revision":
						revision = child.attrib[attr]
					elif attr == "sync-s": # synchronize submodule ... automaticaly
						sync = child.attrib[attr]
						if    sync.lower() == "true" \
						   or sync == "1" \
						   or sync.lower() == "yes":
							sync = True
						elif    sync.lower() == "false" \
						     or sync == "0" \
						     or sync.lower() == "no":
							sync = False
						else:
							debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest : Unknow '" + child.tag + "' attbute : '" + attr + "', value:'" + sync + "' availlable:[true,1,yes,false,0,no]")
					else:
						debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest : Unknow '" + child.tag + "'  attibute : '" + attr + "', availlable:[remote,revision,sync-s]")
				if self.default != None:
					debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest : Node '" + child.tag + "'  already set")
				self.default = {
				    "remote":remote,
				    "revision":revision,
				    "sync":sync,
				    }
				debug.debug("(l:" + str(child.sourceline) + ")     find '" + child.tag + "' : remote='" + remote + "' revision='" + revision + "' sync=" + str(sync));
				continue
			if child.tag == "project":
				name = ""
				path = ""
				for attr in child.attrib:
					if attr == "name":
						name = child.attrib[attr]
					elif attr == "path":
						path = child.attrib[attr]
					else:
						debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest: Unknow '" + child.tag + "'  attibute : '" + attr + "', availlable:[name,revision,sync-s]")
				if name == "":
					debug.error("(l:" + str(child.sourceline) + ") Parsing the manifest: '" + child.tag + "'  missing attribute: 'name' ==> specify the git to clone ...")
				self.projects.append({
				    "name":name,
				    "path":path,
				    })
				debug.debug("(l:" + str(child.sourceline) + ")     find '" + child.tag + "' : name='" + name + "' path='" + path + "'");
				continue
			debug.info("(l:" + str(child.sourceline) + ")     '" + str(child.tag) + "' values=" + str(child.attrib));
			debug.error("(l:" + str(child.sourceline) + ") Parsing error Unknow NODE : '" + str(child.tag) + "' availlable:[remote,include,default,project]")
		# now we parse all sub repo:
		for elem in self.includes:
			elem["manifest"] = Manifest(elem["path"])
		
		
		# inside data    child.text
		
	
	def _create_path_with_elem(self, element):
		path = element["path"]
		if path == "":
			path = element["name"]
			if     len(path) >= 4 \
			   and path[-4:] == ".git":
				path = path[:-4]
		return path
	
	def _check_double_path(self, list_path = [], space=""):
		debug.debug(space + "check path : '" + self.manifest_xml + "'")
		for elem in self.projects:
			path = self._create_path_with_elem(elem)
			debug.debug(space + "    check path:'" + str(path) + "'")
			if path in list_path:
				debug.error("Check Manifest error : double use of the path '" + str(path) + "'")
			list_path.append(path)
		for elem in self.includes:
			elem["manifest"]._check_double_path(list_path, space + "    ")
	
	def get_all_configs(self, default=None, upper_remotes=[]):
		out = []
		if default == None:
			if self.default != None:
				tmp_default = copy.deepcopy(self.default)
			else:
				tmp_default = copy.deepcopy(self.default_base)
		# add all local project
		for elem in self.projects:
			conf = RepoConfig()
			conf.name = elem["name"]
			conf.path = self._create_path_with_elem(elem)
			
			# add default remote for the project (search in herited element)
			for remote in self.remotes:
				if remote["name"] == default["remote"]:
					conf.remotes.append(remote)
			if len(conf.remotes) == 0:
				for remote in upper_remotes:
					if remote["name"] == default["remote"]:
						conf.remotes.append(remote)
			if len(conf.remotes) == 0:
				debug.error("    No remote detected: " + str(len(conf.remotes)) + " for " + conf.name + " with default remote name : " + default["remote"] + " self remote: " + str(self.remotes))
			
			# select default remote:
			conf.select_remote = None
			debug.debug("    remotes count: " + str(len(conf.remotes)))
			for remote in conf.remotes:
				debug.debug("    Ckeck remote : " + remote["name"] + " == " + default["remote"])
				debug.verbose("          remote=" + str(remote))
				debug.verbose("          default=" + str(default))
				if remote["name"] == default["remote"]:
					conf.select_remote = copy.deepcopy(remote)
					# copy the submodule synchronisation
					conf.select_remote["sync"] = default["sync"]
					break
			if conf.select_remote == None:
				debug.error("missing remote for project: " + str(conf.name))
			
			conf.branch = default["revision"]
			out.append(conf)
		# create a temporary variable to transmit the remote to includes
		upper_remotes_forward = copy.deepcopy(upper_remotes)
		for remote in self.remotes:
			upper_remotes_forward.append(remote)
		# add all include project
		for elem in self.includes:
			list_project = elem["manifest"].get_all_configs(tmp_default, upper_remotes_forward)
			for elem_proj in list_project:
				out.append(elem_proj)
		return out


